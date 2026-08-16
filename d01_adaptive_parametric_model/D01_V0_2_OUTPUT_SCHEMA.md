# D01 v0.2 Output Schema

## DMO Required Fields
- model_time
- entity_id
- model_version
- state_level
- state_velocity
- state_acceleration
- state_curvature
- strength
- coherence
- persistence
- perturbation_magnitude
- perturbation_class
- uncertainty
- reversal_propensity
- state_support_ratio
- observation_half_life
- forward_half_life
- parameter_state
- parameter_update_magnitude
- data_quality
- model_health
- dmo_schema_version
- fmo_schema_version
- config_hash
- state_hash
- trace_id

## FMO Required Fields
- model_time
- entity_id
- interval_length
- samples[] with tau, level, velocity, uncertainty, strength, persistence, reversal_propensity
