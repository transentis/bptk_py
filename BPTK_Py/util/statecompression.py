def compress_settings(settings):
    #           scenario_manager: scenario: value_type:  value: [float]
    scenario_managers = dict[str, dict[str, dict[str, dict[str, [float]]]]]()
        
    for step in settings.keys():
        # loop over all scenario managers in the step
        for scenario_manager_name in settings[step]:
            scenario_manager = settings[step][scenario_manager_name]
            
            if not scenario_manager_name in scenario_managers:
                scenario_managers[scenario_manager_name] = dict()
            
            # loop over all scenarios in the current scenario manager for the current step
            for scenario in scenario_manager:
                
                if not scenario in scenario_managers[scenario_manager_name]:
                    scenario_managers[scenario_manager_name][scenario] = dict()
                current_scenario_transformed = scenario_managers[scenario_manager_name][scenario]
                
                # loop over all value types in the current scenario in the current scenario manager for the current step.
                # a value type might for example be "constants"
                for value_type in scenario_manager[scenario]:
                    if not value_type in current_scenario_transformed:
                        current_scenario_transformed[value_type] = dict()
                    
                    # add the values in a flattened format 
                    for constant in scenario_manager[scenario][value_type]:
                        constant_value = scenario_manager[scenario][value_type][constant]
                        if not constant in current_scenario_transformed[value_type]:
                            current_scenario_transformed[value_type][constant] = [constant_value]
                        else:
                            current_scenario_transformed[value_type][constant].append(constant_value)
    return scenario_managers


def compress_results(results):
    #           scenario_manager: scenario: value_name: [float]
    scenario_managers = dict[str, dict[str, dict[str, [float]]]]()
    
    for step in results.keys():
        # loop over all scenario managers in the step
        for scenario_manager_name in results[step]:
            scenario_manager = results[step][scenario_manager_name]
            
            if not scenario_manager_name in scenario_managers:
                scenario_managers[scenario_manager_name] = dict()
            
            # loop over all scenarios in the current scenario manager for the current step
            for scenario in scenario_manager:
                
                if not scenario in scenario_managers[scenario_manager_name]:
                    scenario_managers[scenario_manager_name][scenario] = dict()
                current_scenario_transformed = scenario_managers[scenario_manager_name][scenario]
                
                # loop over all constants in the current scenario in the current scenario manager for the current step.
                # add the constant to the current scenario
                for constant in scenario_manager[scenario]:
                    constant_value = scenario_manager[scenario][constant][step]
                    if not constant in current_scenario_transformed:
                        current_scenario_transformed[constant] = [constant_value]
                    else:
                        current_scenario_transformed[constant].append(constant_value)
    return scenario_managers

def decompress_settings(settings):
    #               step: scenarioManager:  scenario:    constants:   constant: value
    result = dict[str, dict[str, dict[str, dict[str, dict[str, float]]]]]()
    
    for scenario_manager_name in settings.keys():
        for scenario_name in settings[scenario_manager_name]:
            for value_type in settings[scenario_manager_name][scenario_name]:
                for constant_name in settings[scenario_manager_name][scenario_name][value_type]:
                    constant = settings[scenario_manager_name][scenario_name][value_type][constant_name]
                    for i in range(1, len(constant) + 1):
                        # converts int to float in x.0 format (e.g. 3 -> 3.0)
                        step_str = f"{i:.1f}"
                        
                        if not step_str in result:
                            result[step_str] = dict()
                        step_transformed = result[step_str]
                        
                        if not scenario_manager_name in step_transformed:
                            step_transformed[scenario_manager_name] = dict()
                        scenario_manager_transformed = step_transformed[scenario_manager_name]
                        
                        if not scenario_name in scenario_manager_transformed:
                            scenario_manager_transformed[scenario_name] = dict()
                        scenario_transformed = scenario_manager_transformed[scenario_name]
                        
                        if not value_type in scenario_transformed:
                            scenario_transformed[value_type] = dict()
                        value_type_transformed = scenario_transformed[value_type]
                    
                        value_type_transformed[constant_name] = constant[i - 1]
                    
    return result

def decompress_results(results):
    #               step: scenarioManager:  scenario:    constants:   constant: value
    result = dict[str, dict[str, dict[str, dict[str, dict[str, float]]]]]()
    
    for scenario_manager_name in results.keys():
        for scenario_name in results[scenario_manager_name]:
            for constant_name in results[scenario_manager_name][scenario_name]:
                constant = results[scenario_manager_name][scenario_name][constant_name]
                for i in range(1, len(constant) + 1):
                    # converts int to float in x.0 format (e.g. 3 -> 3.0)
                    step_str = f"{i:.1f}"
                    
                    if not step_str in result:
                        result[step_str] = dict()
                    step_transformed = result[step_str]
                    
                    if not scenario_manager_name in step_transformed:
                        step_transformed[scenario_manager_name] = dict()
                    scenario_manager_transformed = step_transformed[scenario_manager_name]
                    
                    if not scenario_name in scenario_manager_transformed:
                        scenario_manager_transformed[scenario_name] = dict()
                    scenario_transformed = scenario_manager_transformed[scenario_name]
                
                    scenario_transformed[constant_name] = {step_str: constant[i - 1]}
                    
    return result