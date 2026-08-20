from __future__ import annotations
import csv,json,os
from pathlib import Path
import numpy as np
from scipy.linalg import expm
ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/'APTF_TEST_012_FP_CANDIDATE_RK45_PROJECTIONS_V0_1.csv';SCORE=ROOT/'APTF_TEST_012_FP_VECTOR_FIELD_SCORECARD_V0_1.csv';PRICE=ROOT/'APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv';P10=ROOT/'APTF_TEST_010_PRICE_ENGINE_EMISSIONS_V0_1.csv';PERT=ROOT/'APTF_TEST_012_FP_PERTURBATION_STABILITY_V0_1.csv';COEF=ROOT/'APTF_TEST_012_FP_COEFFICIENT_STABILITY_V0_1.csv';QUANT=ROOT/'APTF_TEST_012_FP_ERROR_QUANTILES_V0_1.csv';COMP=ROOT/'APTF_TEST_012_BASELINE_VS_CANDIDATE_COMPARISON_V0_1.csv'
price=list(csv.DictReader(PRICE.open(newline='',encoding='utf-8')));em={int(x['observation_index']):x for x in csv.DictReader(P10.open(newline='',encoding='utf-8'))};p=np.array([float(x['price']) for x in price]);p1=np.array([np.nan if x['primary_D1']=='' else float(x['primary_D1']) for x in price]);p2=np.array([np.nan if x['primary_D2']=='' else float(x['primary_D2']) for x in price])
rows=list(csv.DictReader(PROJ.open(newline='',encoding='utf-8')));f0=[x for x in rows if x['candidate_id']=='F0_W15'];common=[int(x['observation_index']) for x in f0]
# Correct F0 actual local 15-row domain evidence.
exits=[];distances=[];coef_rows=[]
for r in f0:
 o=int(r['observation_index']);i=o-1;state=np.array([float(r['projected_P']),float(r['projected_P1']),float(r['projected_P2'])]);X=np.column_stack((p[i-14:i+1],p1[i-14:i+1],p2[i-14:i+1]));lo=X.min(0);hi=X.max(0);m=X.mean(0);s=X.std(0);z=(state-m)/s;inside=np.all((state>=lo)&(state<=hi));r['max_local_domain_distance']=float(np.linalg.norm(z));r['local_envelope_exit_flag']=str(not inside).lower();exits.append(not inside);distances.append(float(np.linalg.norm(z)))
 e=em[o];beta=np.array(json.loads(e['local_model_parameters_json']));sc=json.loads(e['local_model_scaling_json']);physical=beta[1:4]/np.array(sc['state_scales']);eig=np.linalg.eigvals(np.array([[0,1,0],[0,0,1],physical]));coef_rows.append({'candidate':'F0_W15','observation':o,'coefficients':e['local_model_parameters_json'],'coefficient_norm':float(np.linalg.norm(beta)),'condition_number':e['model_condition'],'max_real_eigenvalue':float(eig.real.max()),'spectral_radius':float(abs(eig).max()),'subsequent_P2_error':r['error_P2']})
# Rewrite projections only for corrected F0 fields.
tmp=PROJ.with_suffix('.tmp');
with tmp.open('w',newline='',encoding='utf-8') as h:
 w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
os.replace(tmp,PROJ)
# F0 perturbation on deterministic 128 common rows.
pert=[];amps=[]
for o in [common[int(x)] for x in np.linspace(0,len(common)-1,128,dtype=int)]:
 e=em[o];beta=np.array(json.loads(e['local_model_parameters_json']));sc=json.loads(e['local_model_scaling_json']);physical=beta[1:4]/np.array(sc['state_scales']);A=np.array([[0,1,0],[0,0,1],physical]);M=expm(A);scales=np.array(sc['state_scales'])
 for k,name in enumerate(('P','P1','P2')):
  delta=1e-6*scales[k];amp=float(np.linalg.norm(M[:,k]*delta)/delta);amps.append(amp);pert.append({'candidate':'F0_W15','observation':o,'perturbed_component':name,'perturbation_magnitude':delta,'baseline_final_state':'LINEAR_AFFINE_DIFFERENCE','perturbed_final_state':'LINEAR_AFFINE_DIFFERENCE','amplification_ratio':amp})
with PERT.open('a',newline='',encoding='utf-8') as h:csv.DictWriter(h,fieldnames=list(pert[0])).writerows(pert)
with COEF.open('a',newline='',encoding='utf-8') as h:csv.DictWriter(h,fieldnames=list(coef_rows[0])).writerows(coef_rows)
# Update F0 scorecard.
scores=list(csv.DictReader(SCORE.open(newline='',encoding='utf-8')));f=next(x for x in scores if x['candidate_id']=='F0_W15');f['perturbation_median_amplification']=np.median(amps);f['perturbation_Q95']=np.quantile(amps,.95);f['perturbation_Q99']=np.quantile(amps,.99);f['perturbation_maximum']=max(amps);f['local_envelope_exit_rate']=np.mean(exits);eig=np.array([float(x['max_real_eigenvalue']) for x in coef_rows]);f['median_max_real_eigenvalue']=np.median(eig);f['Q99_max_real_eigenvalue']=np.quantile(eig,.99)
with SCORE.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
# Append transition-proximity quantiles for every candidate.
crossings={int(x['observation_index']) for x in csv.DictReader(open(ROOT/'APTF_TEST_009_DERIVATIVE_CROSSINGS_V0_1.csv',newline='',encoding='utf-8'))};quant_rows=[]
by={}
for r in rows:by.setdefault(r['candidate_id'],[]).append(r)
for cid,items in by.items():
 for label,selector in [('AT_TRANSITION',lambda o:o+1 in crossings),('ONE_BEFORE_TRANSITION',lambda o:o+2 in crossings),('ONE_AFTER_TRANSITION',lambda o:o in crossings),('FAR',lambda o:o not in crossings and o+1 not in crossings and o+2 not in crossings)]:
  values=np.array([abs(float(r['error_P2'])) for r in items if selector(int(r['observation_index']))]);
  if not len(values):continue
  q=lambda x:float(np.quantile(values,x));quant_rows.append({'candidate':cid,'window':int(cid.rsplit('W',1)[1]),'stratum_type':'TRANSITION_PROXIMITY','stratum':label,'count':len(values),'Q50':q(.5),'Q75':q(.75),'Q90':q(.9),'Q95':q(.95),'Q99':q(.99),'Q99_5':q(.995),'Q99_9':q(.999),'maximum':values.max()})
with QUANT.open('a',newline='',encoding='utf-8') as h:csv.DictWriter(h,fieldnames=list(quant_rows[0])).writerows(quant_rows)
# Rebuild baseline comparison from corrected scorecard.
f0row=next(x for x in scores if x['candidate_id']=='F0_W15');comparison=[];score_fields=list(scores[0])
for x in scores:comparison.append({'baseline':'F0_W15','candidate':x['candidate_id'],**{f'F0_{k}':f0row[k] for k in score_fields if k not in ('candidate_id','family','window')},**{f'candidate_{k}':x[k] for k in score_fields if k not in ('candidate_id','family','window')}})
with COMP.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(comparison[0]));w.writeheader();w.writerows(comparison)
print(json.dumps({'F0_exit_rate':float(np.mean(exits)),'F0_perturb_Q99':float(np.quantile(amps,.99)),'transition_quantile_rows':len(quant_rows)},indent=2))
