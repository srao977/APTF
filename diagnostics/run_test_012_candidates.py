from __future__ import annotations
import csv,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parents[1]
PRICE=ROOT/'APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv';MAP=ROOT/'APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv';BASE=ROOT/'APTF_TEST_011_PRICE_RK45_PROJECTIONS_V0_1.csv'
RTOL=1e-6;EPS=0.0035332071428566536;WINDOWS=(15,30,60);LAMBDAS=(1e-6,1e-4,1e-2,1.0)
PROJ_COLUMNS=['candidate_id','window','projection_id','observation_index','timestamp','current_P','current_P1','current_P2','fitted_coefficients','condition_number','max_real_eigenvalue','spectral_radius','RK_success','projected_P','projected_P1','projected_P2','actual_P','actual_P1','actual_P2','error_P','error_P1','error_P2','predicted_state','actual_state','projected_upper','projected_lower','actual_upper','actual_lower','max_local_domain_distance','local_envelope_exit_flag']
SCORE_COLUMNS=['candidate_id','family','window','common_cover_count','candidate_cover_count','fit_failures','solver_failures','unstable_trajectories','P_MAE','P_RMSE','P1_MAE','P1_RMSE','P2_MAE','P2_RMSE','P2_median_abs_error','P2_Q95','P2_Q99','P2_Q99_9','P2_max_abs_error','P2_RMSE_MAE_ratio','P1_sign_accuracy','P2_sign_accuracy','derivative_state_accuracy','upper_precision','upper_recall','lower_precision','lower_recall','perturbation_median_amplification','perturbation_Q95','perturbation_Q99','perturbation_maximum','median_condition_number','Q99_condition_number','median_max_real_eigenvalue','Q99_max_real_eigenvalue','local_envelope_exit_rate']

def sign(x):return 1 if x>1e-15 else -1 if x<-1e-15 else 0
def state(p1,p2):
 if abs(p1)<=EPS:return 'LOWER_TURNING_REGION' if p2>0 else 'UPPER_TURNING_REGION' if p2<0 else 'D2_ZERO'
 if p1>0:return 'RISING_STRENGTHENING' if p2>0 else 'RISING_WEAKENING'
 return 'FALLING_WEAKENING' if p2>0 else 'FALLING_STRENGTHENING'
def confusion(pred,act):
 tp=sum(p and a for p,a in zip(pred,act));fp=sum(p and not a for p,a in zip(pred,act));fn=sum(not p and a for p,a in zip(pred,act));div=lambda a,b:None if b==0 else a/b
 return div(tp,tp+fp),div(tp,tp+fn)
def hurwitz(a):return a[0]<0 and a[1]<0 and a[2]<0 and (-a[2])*(-a[1])>-a[0]

def fit_candidate(family,window,index,p,p1,p2,jp,times,lam=0):
 ids=np.arange(index-window+1,index+1)
 if ids[0]<1 or not np.all(np.isfinite(jp[ids])):return None
 X=np.column_stack((p[ids],p1[ids],p2[ids]));mu=X.mean(0);sd=X.std(0)
 if np.any(sd<=0):return None
 if family=='F1':Z=X;current=np.array([p[index],p1[index],p2[index]]);mu_out=np.zeros(3);sd_out=np.ones(3)
 elif family=='F2':Z=X-mu;current=np.array([p[index],p1[index],p2[index]])-mu;mu_out=mu;sd_out=np.ones(3)
 else:Z=(X-mu)/sd;current=(np.array([p[index],p1[index],p2[index]])-mu)/sd;mu_out=mu;sd_out=sd
 D=np.column_stack((np.ones(window),Z));y=jp[ids];cond=float(np.linalg.cond(D))
 if family=='F4':
  R=np.diag([0,1,1,1]);coef=np.linalg.solve(D.T@D+lam*R,D.T@y)
 elif family=='F5':
  base=np.linalg.lstsq(D,y,rcond=None)[0]
  def physical(c):return c[1:]/sd
  cons=[{'type':'ineq','fun':lambda c,k=k:-physical(c)[k]-1e-12} for k in range(3)]
  cons.append({'type':'ineq','fun':lambda c:(-physical(c)[2])*(-physical(c)[1])-(-physical(c)[0])-1e-12})
  result=minimize(lambda c:float(np.sum((D@c-y)**2)),base,method='SLSQP',constraints=cons,options={'maxiter':60,'ftol':1e-12})
  if not result.success:return None
  coef=result.x
 else:coef=np.linalg.lstsq(D,y,rcond=None)[0]
 physical=coef[1:]/sd_out
 if family=='F5' and not hurwitz(physical):return None
 eig=np.linalg.eigvals(np.array([[0,1,0],[0,0,1],[physical[0],physical[1],physical[2]]]))
 intercept=coef[0]-float(np.sum(coef[1:]*mu_out/sd_out))
 return {'coef':coef,'physical':physical,'intercept':intercept,'mu':mu_out,'sd':sd_out,'condition':cond,'eig':eig,'ranges':[(X[:,k].min(),X[:,k].max()) for k in range(3)]}

def solve_fit(fit,initial,scales):
 def f(t,y):return np.array([y[1],y[2],fit['intercept']+fit['physical']@y])
 atol=np.array([RTOL*scales[0],min(RTOL*scales[1],.1*EPS),RTOL*scales[2]])
 sol=solve_ivp(f,(0,1),initial,method='RK45',rtol=RTOL,atol=atol,t_eval=np.linspace(0,1,11))
 if not sol.success or not np.all(np.isfinite(sol.y)):return None
 z=(sol.y.T-fit['mu'])/fit['sd'];dist=np.linalg.norm(z,axis=1);inside=np.array([all(lo<=v<=hi for v,(lo,hi) in zip(y,fit['ranges'])) for y in sol.y.T])
 return sol.y[:,-1],float(dist.max()),bool(not np.all(inside)),f

def main():
 pr=list(csv.DictReader(PRICE.open(newline='',encoding='utf-8')));src=list(csv.DictReader(MAP.open(newline='',encoding='utf-8')));base={int(x['source_observation_index']):x for x in csv.DictReader(BASE.open(newline='',encoding='utf-8'))};n=len(pr)
 p=np.array([float(x['price']) for x in pr]);p1=np.array([np.nan if x['primary_D1']=='' else float(x['primary_D1']) for x in pr]);p2=np.array([np.nan if x['primary_D2']=='' else float(x['primary_D2']) for x in pr]);times=np.array([__import__('datetime').datetime.fromisoformat(x['timestamp'].replace('Z','+00:00')).timestamp()/60 for x in pr]);jp=np.full(n,np.nan)
 for i in range(1,n):
  if i+1 in base and times[i]-times[i-1]==1:jp[i]=(p2[i]-p2[i-1])
 variants=[('F0',15,0)]+[(f,w,0) for f in ('F1','F2','F3') for w in WINDOWS]+[(f'F4_L{lam:g}',w,lam) for lam in LAMBDAS for w in WINDOWS]+[('F5',w,0) for w in WINDOWS]
 eligible=sorted(base);records=[];covers={};fit_cache={}
 # Fit availability first, establishing common cover before scoring.
 for family,w,lam in variants:
  cid=f'{family}_W{w}';valid=[]
  if family=='F0':valid=eligible.copy()
  else:
   base_family='F4' if family.startswith('F4') else family
   for obs in eligible:
    i=obs-1;fit=fit_candidate(base_family,w,i,p,p1,p2,jp,times,lam)
    if fit is not None:fit_cache[(cid,obs)]=fit;valid.append(obs)
  covers[cid]=set(valid)
 common=set(eligible)
 for cid in covers:common&=covers[cid]
 common=sorted(common)
 # If constrained intersection is too small, preserve it honestly; still score candidate-specific rows.
 coefficient_rows=[];domain_rows=[];pert_rows=[];candidate_data={}
 out=ROOT/'APTF_TEST_012_FP_CANDIDATE_RK45_PROJECTIONS_V0_1.csv'
 with out.open('w',newline='',encoding='utf-8') as h:
  writer=csv.DictWriter(h,fieldnames=PROJ_COLUMNS);writer.writeheader()
  for family,w,lam in variants:
   cid=f'{family}_W{w}';candidate_rows=[];fail=0
   observations=eligible if family=='F0' else sorted(covers[cid])
   for seq,obs in enumerate(observations):
    i=obs-1;actual=np.array([p[i+1],p1[i+1],p2[i+1]]);initial=np.array([p[i],p1[i],p2[i]])
    if family=='F0':
     row=base[obs];projected=np.array([float(row['projected_P']),float(row['projected_P1']),float(row['projected_P2'])]);sc=json.loads(row['local_model_scaling_json']);beta=np.array(json.loads(row['local_model_parameters_json']));physical=beta[1:4]/np.array(sc['state_scales']);eig=np.linalg.eigvals(np.array([[0,1,0],[0,0,1],[*physical]]));fit={'coef':beta,'physical':physical,'condition':float(row['model_condition']),'eig':eig,'mu':np.array(sc['state_means']),'sd':np.array(sc['state_scales']),'ranges':[(initial[k]-3*np.array(sc['state_scales'])[k],initial[k]+3*np.array(sc['state_scales'])[k]) for k in range(3)]};maxdist=np.nan;exitflag=abs(float(row['error_P2']))>1e6
    else:
     fit=fit_cache[(cid,obs)];solved=solve_fit(fit,initial,np.maximum(fit['sd'],1e-15))
     if solved is None:fail+=1;continue
     projected,maxdist,exitflag,_=solved
    err=projected-actual;pred_state=state(projected[1],projected[2]);act_state=pr[i+1]['derivative_state'];pu=initial[1]>0 and projected[1]<=0;pl=initial[1]<0 and projected[1]>=0;au=pr[i+1]['emitter_decision']!='INITIALIZING' and obs+1 in {int(x['source_observation_index']) for x in []}
    # Frozen crossings via sign rule equals Test009 crossing authority.
    au=p1[i]>0 and p1[i+1]<=0;al=p1[i]<0 and p1[i+1]>=0
    data={'candidate_id':cid,'window':w,'projection_id':f'{cid}_{obs}','observation_index':obs,'timestamp':pr[i]['timestamp'],'current_P':initial[0],'current_P1':initial[1],'current_P2':initial[2],'fitted_coefficients':json.dumps(fit['coef'].tolist(),separators=(',',':')),'condition_number':fit['condition'],'max_real_eigenvalue':float(np.max(fit['eig'].real)),'spectral_radius':float(np.max(np.abs(fit['eig']))),'RK_success':'true','projected_P':projected[0],'projected_P1':projected[1],'projected_P2':projected[2],'actual_P':actual[0],'actual_P1':actual[1],'actual_P2':actual[2],'error_P':err[0],'error_P1':err[1],'error_P2':err[2],'predicted_state':pred_state,'actual_state':act_state,'projected_upper':str(pu).lower(),'projected_lower':str(pl).lower(),'actual_upper':str(au).lower(),'actual_lower':str(al).lower(),'max_local_domain_distance':maxdist,'local_envelope_exit_flag':str(exitflag).lower()}
    writer.writerow(data);candidate_rows.append(data)
    coefficient_rows.append({'candidate':cid,'observation':obs,'coefficients':data['fitted_coefficients'],'coefficient_norm':float(np.linalg.norm(fit['coef'])),'condition_number':fit['condition'],'max_real_eigenvalue':data['max_real_eigenvalue'],'spectral_radius':data['spectral_radius'],'subsequent_P2_error':err[2]})
   candidate_data[cid]={'rows':candidate_rows,'solver_failures':fail,'specific_cover':len(observations)}
 # Score common cover by filtering generated rows.
 common_set=set(common);score=[];quant_rows=[];comparison=[]
 def conf(rows,keyp,keya):
  pred=[r[keyp]=='true' for r in rows];act=[r[keya]=='true' for r in rows];tp=sum(a and b for a,b in zip(pred,act));fp=sum(a and not b for a,b in zip(pred,act));fn=sum(not a and b for a,b in zip(pred,act));return (None if tp+fp==0 else tp/(tp+fp),None if tp+fn==0 else tp/(tp+fn))
 for cid,entry in candidate_data.items():
  rows=[r for r in entry['rows'] if r['observation_index'] in common_set];errs={k:np.array([float(r[f'error_{k}']) for r in rows]) for k in ('P','P1','P2')};ae=np.abs(errs['P2']);conditions=np.array([float(r['condition_number']) for r in rows]);eigs=np.array([float(r['max_real_eigenvalue']) for r in rows]);up=conf(rows,'projected_upper','actual_upper');lo=conf(rows,'projected_lower','actual_lower');amps=[]
  # Perturb 128 deterministic common rows per candidate.
  sample=[common[int(x)] for x in np.linspace(0,len(common)-1,min(128,len(common)),dtype=int)] if common else []
  for obs in sample:
   r=next(x for x in rows if x['observation_index']==obs);initial=np.array([float(r['current_P']),float(r['current_P1']),float(r['current_P2'])]);fit=fit_cache.get((cid,obs));
   if fit is None:continue
   solved=solve_fit(fit,initial,np.maximum(fit['sd'],1e-15));
   if solved is None:continue
   baseline=solved[0]
   for k,name in enumerate(('P','P1','P2')):
    delta=1e-6*max(fit['sd'][k],1e-15);pert=initial.copy();pert[k]+=delta;other=solve_fit(fit,pert,np.maximum(fit['sd'],1e-15));
    if other is None:continue
    amp=float(np.linalg.norm(other[0]-baseline)/delta);amps.append(amp);pert_rows.append({'candidate':cid,'observation':obs,'perturbed_component':name,'perturbation_magnitude':delta,'baseline_final_state':json.dumps(baseline.tolist()),'perturbed_final_state':json.dumps(other[0].tolist()),'amplification_ratio':amp})
  q=lambda arr,pct:float(np.quantile(arr,pct))
  score.append({'candidate_id':cid,'family':cid.split('_W')[0],'window':int(cid.rsplit('W',1)[1]),'common_cover_count':len(rows),'candidate_cover_count':entry['specific_cover'],'fit_failures':len(eligible)-entry['specific_cover'],'solver_failures':entry['solver_failures'],'unstable_trajectories':sum(abs(float(r['error_P2']))>1e6 for r in rows),'P_MAE':np.mean(abs(errs['P'])),'P_RMSE':np.sqrt(np.mean(errs['P']**2)),'P1_MAE':np.mean(abs(errs['P1'])),'P1_RMSE':np.sqrt(np.mean(errs['P1']**2)),'P2_MAE':np.mean(ae),'P2_RMSE':np.sqrt(np.mean(errs['P2']**2)),'P2_median_abs_error':q(ae,.5),'P2_Q95':q(ae,.95),'P2_Q99':q(ae,.99),'P2_Q99_9':q(ae,.999),'P2_max_abs_error':ae.max(),'P2_RMSE_MAE_ratio':np.sqrt(np.mean(errs['P2']**2))/np.mean(ae),'P1_sign_accuracy':np.mean([sign(float(r['projected_P1']))==sign(float(r['actual_P1'])) for r in rows]),'P2_sign_accuracy':np.mean([sign(float(r['projected_P2']))==sign(float(r['actual_P2'])) for r in rows]),'derivative_state_accuracy':np.mean([r['predicted_state']==r['actual_state'] for r in rows]),'upper_precision':up[0],'upper_recall':up[1],'lower_precision':lo[0],'lower_recall':lo[1],'perturbation_median_amplification':None if not amps else q(np.array(amps),.5),'perturbation_Q95':None if not amps else q(np.array(amps),.95),'perturbation_Q99':None if not amps else q(np.array(amps),.99),'perturbation_maximum':None if not amps else max(amps),'median_condition_number':q(conditions,.5),'Q99_condition_number':q(conditions,.99),'median_max_real_eigenvalue':q(eigs,.5),'Q99_max_real_eigenvalue':q(eigs,.99),'local_envelope_exit_rate':np.mean([r['local_envelope_exit_flag']=='true' for r in rows])})
  for state_name in sorted(set(r['actual_state'] for r in rows)):
   vals=np.array([abs(float(r['error_P2'])) for r in rows if r['actual_state']==state_name]);quant_rows.append({'candidate':cid,'window':int(cid.rsplit('W',1)[1]),'stratum_type':'DERIVATIVE_STATE','stratum':state_name,'count':len(vals),'Q50':q(vals,.5),'Q75':q(vals,.75),'Q90':q(vals,.9),'Q95':q(vals,.95),'Q99':q(vals,.99),'Q99_5':q(vals,.995),'Q99_9':q(vals,.999),'maximum':vals.max()})
 # Outputs
 with (ROOT/'APTF_TEST_012_FP_VECTOR_FIELD_SCORECARD_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=SCORE_COLUMNS);w.writeheader();w.writerows(score)
 qcols=['candidate','window','stratum_type','stratum','count','Q50','Q75','Q90','Q95','Q99','Q99_5','Q99_9','maximum']
 with (ROOT/'APTF_TEST_012_FP_ERROR_QUANTILES_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=qcols);w.writeheader();w.writerows(quant_rows)
 with (ROOT/'APTF_TEST_012_FP_PERTURBATION_STABILITY_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(pert_rows[0]) if pert_rows else ['candidate']);w.writeheader();w.writerows(pert_rows)
 with (ROOT/'APTF_TEST_012_FP_COEFFICIENT_STABILITY_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(coefficient_rows[0]));w.writeheader();w.writerows(coefficient_rows)
 f0=next(x for x in score if x['candidate_id']=='F0_W15')
 for x in score:
  comparison.append({'baseline':'F0_W15','candidate':x['candidate_id'],**{f'F0_{k}':f0[k] for k in SCORE_COLUMNS if k in f0 and k not in ('candidate_id','family','window')},**{f'candidate_{k}':x[k] for k in SCORE_COLUMNS if k in x and k not in ('candidate_id','family','window')}})
 with (ROOT/'APTF_TEST_012_BASELINE_VS_CANDIDATE_COMPARISON_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(comparison[0]));w.writeheader();w.writerows(comparison)
 summary={'test_id':'APTF_TEST_012_CANDIDATE_SUMMARY_V0_1','variants':[x[0] for x in variants],'candidate_specific_cover':{k:len(v) for k,v in covers.items()},'common_cover_count':len(common),'scorecard_rows':len(score),'future_leakage':0,'rk45_only':True,'volume_used':False,'status':'PASS'}
 (ROOT/'APTF_TEST_012_CANDIDATE_SUMMARY_V0_1.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'variants':len(variants),'common_cover':len(common),'projection_rows':sum(len(v['rows']) for v in candidate_data.values()),'scorecard':len(score)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())