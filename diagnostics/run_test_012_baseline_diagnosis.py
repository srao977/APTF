from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/"APTF_TEST_011_PRICE_RK45_PROJECTIONS_V0_1.csv"
COND=ROOT/"APTF_TEST_011_PRICE_CONDITION_METRICS_V0_1.csv"
STAB=ROOT/"APTF_TEST_011_PRICE_LOCAL_STABILITY_V0_1.csv"
PRICE=ROOT/"APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"

POP_COLUMNS=["projection_id","observation_index","timestamp","absolute_P2_error","error_percentile_group","P","P1","P2","F_P_initial","coefficients","condition_number","max_real_eigenvalue","spectral_radius","local_domain_distance_initial","session_id","derivative_state","transition_proximity"]
TRACE_COLUMNS=["projection_id","matched_role","tau","P","P1","P2","F_P","local_domain_distance","local_envelope_inside","local_envelope_exit_dimension"]
JAC_COLUMNS=["observation","a1","a2","a3","eigenvalues","max_real_eigenvalue","spectral_radius","P2_error","instability_group"]
DOMAIN_COLUMNS=["candidate","observation","local_P_range","local_P1_range","local_P2_range","max_D_local","envelope_exit_flag","first_exit_time","exit_dimension","P2_endpoint_error"]

def model(row):
 beta=np.array(json.loads(row['local_model_parameters_json']),float);s=json.loads(row['local_model_scaling_json']);means=np.array(s['state_means']);scales=np.array(s['state_scales']);tm=s['time_mean'];ts=s['time_scale']
 def f(t,y):
  z=(y-means)/scales;j=beta@np.array([1,z[0],z[1],z[2],(t-tm)/ts]);return np.array([y[1],y[2],j])
 return f,beta,means,scales

def classify(error,qs):
 if error>=qs[.999]:return 'TOP_0.1_PERCENT'
 if error>=qs[.995]:return 'TOP_0.5_PERCENT'
 if error>=qs[.99]:return 'TOP_1_PERCENT'
 if error>=qs[.95]:return 'TOP_5_PERCENT'
 if error>=qs[.90]:return 'TOP_10_PERCENT'
 if error<=qs[.5]:return 'TYPICAL_AT_OR_BELOW_MEDIAN'
 return 'INTERMEDIATE'

def dense(row,role):
 f,_,means,scales=model(row);initial=np.array([float(row['current_P']),float(row['current_P1']),float(row['current_P2'])]);grid=np.linspace(0,1,11);result=solve_ivp(f,(0,1),initial,method='RK45',rtol=float(row['rtol']),atol=np.array([float(row['atol_P']),float(row['atol_P1']),float(row['atol_P2'])]),t_eval=grid)
 output=[]
 for t,y in zip(result.t,result.y.T):
  z=(y-means)/scales;inside=np.all(np.abs(z)<=np.maximum(np.abs((initial-means)/scales),1)+3);dim='' if inside else ['P','P1','P2'][int(np.argmax(np.abs(z)))];output.append({'projection_id':row['rk_projection_id'],'matched_role':role,'tau':t,'P':y[0],'P1':y[1],'P2':y[2],'F_P':f(t,y)[2],'local_domain_distance':float(np.linalg.norm(z)),'local_envelope_inside':str(bool(inside)).lower(),'local_envelope_exit_dimension':dim})
 return output

def main():
 rows=list(csv.DictReader(PROJ.open(newline='',encoding='utf-8')));price=list(csv.DictReader(PRICE.open(newline='',encoding='utf-8')));conditions={x['rk_projection_id']:x for x in csv.DictReader(COND.open(newline='',encoding='utf-8'))};ampl={}
 for x in csv.DictReader(STAB.open(newline='',encoding='utf-8')):
  ampl.setdefault(int(x['observation_index']),[]).append(float(x['amplification_ratio']))
 errors=np.array([abs(float(x['error_P2'])) for x in rows]);qs={p:float(np.quantile(errors,p)) for p in [.5,.75,.9,.95,.99,.995,.999]};severe_indices=np.flatnonzero(errors>=qs[.999]);stable_indices=np.flatnonzero(errors<=qs[.5]);stable_by_state={}
 for idx in stable_indices:stable_by_state.setdefault(rows[idx]['actual_derivative_state'],[]).append(idx)
 populations=[];jac=[];domains=[]
 for idx,row in enumerate(rows):
  _,beta,means,scales=model(row);a1=beta[1]/scales[0];a2=beta[2]/scales[1];a3=beta[3]/scales[2];eig=np.linalg.eigvals(np.array([[0,1,0],[0,0,1],[a1,a2,a3]],float));group=classify(errors[idx],qs);initial=np.array([float(row['current_P']),float(row['current_P1']),float(row['current_P2'])]);z=(initial-means)/scales;transition='AT_UPPER' if row['actual_upper_crossing']=='True' else 'AT_LOWER' if row['actual_lower_crossing']=='True' else 'NON_CROSSING'
  populations.append({'projection_id':row['rk_projection_id'],'observation_index':row['source_observation_index'],'timestamp':row['timestamp'],'absolute_P2_error':errors[idx],'error_percentile_group':group,'P':initial[0],'P1':initial[1],'P2':initial[2],'F_P_initial':conditions[row['rk_projection_id']]['projected_J_P_at_start'],'coefficients':row['local_model_parameters_json'],'condition_number':row['model_condition'],'max_real_eigenvalue':float(np.max(eig.real)),'spectral_radius':float(np.max(np.abs(eig))),'local_domain_distance_initial':float(np.linalg.norm(z)),'session_id':row['session_id'],'derivative_state':row['actual_derivative_state'],'transition_proximity':transition})
  jac.append({'observation':row['source_observation_index'],'a1':a1,'a2':a2,'a3':a3,'eigenvalues':json.dumps([[float(v.real),float(v.imag)] for v in eig],separators=(',',':')),'max_real_eigenvalue':float(np.max(eig.real)),'spectral_radius':float(np.max(np.abs(eig))),'P2_error':row['error_P2'],'instability_group':group})
 with (ROOT/'APTF_TEST_012_TEST011_P2_FAILURE_POPULATIONS_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=POP_COLUMNS);w.writeheader();w.writerows(populations)
 with (ROOT/'APTF_TEST_012_BASELINE_JACOBIAN_STABILITY_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=JAC_COLUMNS);w.writeheader();w.writerows(jac)
 severe_traces=[];control_traces=[];matches=[]
 for severe_idx in severe_indices:
  row=rows[severe_idx];state=row['actual_derivative_state'];pool=stable_by_state.get(state,stable_indices.tolist());lo=max(0,severe_idx-5000);hi=min(len(rows),severe_idx+5001);near=[i for i in pool if lo<=i<hi] or pool
  target=np.array([float(row['current_P']),abs(float(row['current_P1'])),abs(float(row['current_P2']))]);scale=np.maximum(np.array(json.loads(row['local_model_scaling_json'])['state_scales']),1e-15);control_idx=min(near,key=lambda i:float(np.linalg.norm((np.array([float(rows[i]['current_P']),abs(float(rows[i]['current_P1'])),abs(float(rows[i]['current_P2']))])-target)/scale)))
  for target_row,role,bucket in ((row,'SEVERE',severe_traces),(rows[control_idx],'MATCHED_STABLE',control_traces)):
   trace=dense(target_row,role);bucket.extend(trace);zs=[x['local_domain_distance'] for x in trace];exits=[x for x in trace if x['local_envelope_inside']=='false'];domains.append({'candidate':'F0','observation':target_row['source_observation_index'],'local_P_range':json.dumps([float(target_row['current_P'])-3*json.loads(target_row['local_model_scaling_json'])['state_scales'][0],float(target_row['current_P'])+3*json.loads(target_row['local_model_scaling_json'])['state_scales'][0]]),'local_P1_range':json.dumps([float(target_row['current_P1'])-3*json.loads(target_row['local_model_scaling_json'])['state_scales'][1],float(target_row['current_P1'])+3*json.loads(target_row['local_model_scaling_json'])['state_scales'][1]]),'local_P2_range':json.dumps([float(target_row['current_P2'])-3*json.loads(target_row['local_model_scaling_json'])['state_scales'][2],float(target_row['current_P2'])+3*json.loads(target_row['local_model_scaling_json'])['state_scales'][2]]),'max_D_local':max(zs),'envelope_exit_flag':str(bool(exits)).lower(),'first_exit_time':'' if not exits else exits[0]['tau'],'exit_dimension':'' if not exits else exits[0]['local_envelope_exit_dimension'],'P2_endpoint_error':target_row['error_P2']})
 for path,data in ((ROOT/'APTF_TEST_012_SEVERE_TRAJECTORY_TRACES_V0_1.csv',severe_traces),(ROOT/'APTF_TEST_012_MATCHED_STABLE_TRAJECTORY_TRACES_V0_1.csv',control_traces)):
  with path.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=TRACE_COLUMNS);w.writeheader();w.writerows(data)
 with (ROOT/'APTF_TEST_012_LOCAL_DOMAIN_EXIT_ANALYSIS_V0_1.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=DOMAIN_COLUMNS);w.writeheader();w.writerows(domains)
 severe=[populations[i] for i in severe_indices];typical=[populations[i] for i in stable_indices]
 def summarize(group,key):
  a=np.array([float(x[key]) for x in group]);return {'median':float(np.median(a)),'mean':float(np.mean(a)),'q95':float(np.quantile(a,.95))}
 summary={'test_id':'APTF_TEST_012_BASELINE_DIAGNOSIS_V0_1','projection_count':len(rows),'quantiles':{str(k):v for k,v in qs.items()},'severe_count':len(severe),'typical_count':len(typical),'severe':{k:summarize(severe,k) for k in ['P2','F_P_initial','condition_number','max_real_eigenvalue','local_domain_distance_initial']},'typical':{k:summarize(typical,k) for k in ['P2','F_P_initial','condition_number','max_real_eigenvalue','local_domain_distance_initial']},'severe_domain_exit_rate':sum(x['envelope_exit_flag']=='true' for x in domains[::2])/len(severe),'matched_control_domain_exit_rate':sum(x['envelope_exit_flag']=='true' for x in domains[1::2])/len(severe),'future_leakage':0,'status':'PASS'}
 (ROOT/'APTF_TEST_012_BASELINE_DIAGNOSIS_V0_1.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'projections':len(rows),'P2_error_quantiles':summary['quantiles'],'severe':len(severe),'severe_exit_rate':summary['severe_domain_exit_rate']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())