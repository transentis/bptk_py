Developing Dashboards Using the SimpleDashboard Utility Class
=============================================================

One of BPTK’s biggest strengths is the ability to easily create
interactive dashboards. The simple dashboard class in BPTK allows the
user to create complex, interactive dashboards with minimum coding
requirements.

Creating the model
------------------

First, we need a BPTK model, let’s create one.

We need to do all necessary imports and instantiate the model:

.. code:: ipython3

    from BPTK_Py import Model
    import BPTK_Py
    
    model = Model(starttime=0.0, stoptime=20.0, dt=1.0, name="Test Model")

Next, we have to define the model. The model calculates an account
balance given a salary and a tax rate.

.. code:: ipython3

    stock = model.stock("balance")
    taxes_accumulated = model.stock("tax_acc")
    
    income = model.flow("income")
    taxes = model.flow("taxes")
    
    constantSalary = model.constant("salary")
    constantTax = model.constant("tax")
    constantTax.equation = 0.0
    constantSalary.equation = 0.0
    
    stock.equation = income - taxes
    income.equation = constantSalary # income - tax
    taxes.equation = constantSalary * constantTax
    
    taxes_accumulated.equation = taxes

Lastly we have to register a scenario manager and scenario in BPTK.

.. code:: ipython3

    scenario_manager = {"sm": {"model": model}}
    
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager(scenario_manager)
    bptk.register_scenarios(
        scenario_manager="sm",
        scenarios=
        {
            "testScenario":{}
        }
    )

Next we want to display the output using an interactive dashboard.

Display output
--------------

The simple dashboard class automatically handles plot updates, connects
widgets to the model and handles widget updating. You can create
dashboards without the simple dashboard class, but that is not
recommended.

First, we have to import and instantiate the SimpleDashboard class. It
requires both the scenario manager and scenario.

.. code:: ipython3

    from BPTK_Py.visualizations import SimpleDashboard
    import ipywidgets as widgets
    
    dashboard = SimpleDashboard(bptk, scenario_manager="sm", scenario="testScenario")

Now we have to create a few widgets. We need two sliders to update the
tax rate and salary. When the sliders change, a graph plotting the
balance is updated.

.. code:: ipython3

    wdg_tax_slider = widgets.FloatSlider(description="Tax rate", min=0.0, max=1.0, value=0.2, step=0.01)
    wdg_salary_slider = widgets.FloatSlider(description="Salary", min=0.0, max=1000.0, value=100.0, step=1.0)
    
    dashboard.add_widget(wdg_tax_slider, "tax")
    dashboard.add_widget(wdg_salary_slider, "salary")
    
    plot = dashboard.add_plot(
        equations=["balance"], 
        names=["Balance"],
        title="Account Balance",
        x_label="Months",
        y_label="Balance",
    )
    
    controls = widgets.VBox([wdg_tax_slider, wdg_salary_slider])
    display(plot)
    display(controls)
    dashboard.start()



.. parsed-literal::

    Output()



.. parsed-literal::

    VBox(children=(FloatSlider(value=0.2, description='Tax rate', max=1.0, step=0.01), FloatSlider(value=100.0, de…


It would be useful to see how much of the salary gets paid as taxes (in
absolute terms). Luckily, adding multiple graphs is trivial.

.. code:: ipython3

    plot2 = dashboard.add_plot(
        equations=["tax_acc"], 
        names=["Taxes"],
        title="Paid Taxes",
        x_label="Months",
        y_label="Taxes",
    )
    
    graph_tabs = widgets.Tab(children = [plot, plot2])
    graph_tabs.set_title(0, 'Balance')
    graph_tabs.set_title(1, 'Taxes')
    
    display(graph_tabs)
    display(controls)
    dashboard.start()



.. parsed-literal::

    Tab(children=(Output(outputs=({'output_type': 'display_data', 'data': {'text/plain': '<Figure size 1440x720 wi…



.. parsed-literal::

    VBox(children=(FloatSlider(value=0.2, description='Tax rate', max=1.0, step=0.01), FloatSlider(value=100.0, de…


Advanced features
~~~~~~~~~~~~~~~~~

Complex models tend to have more requirements than just updating a graph
when a slider moves.

Callbacks
^^^^^^^^^

This dashboard will show how to use callbacks to execute custom code
when widget values change. In the example below, taxes can be activated
and deactivated using a tick box.

.. code:: ipython3

    
    
    # instantiate dashboard
    dashboard = SimpleDashboard(bptk, scenario_manager="sm", scenario="testScenario")
    
    # Create all widgets
    wdg_salary_slider = widgets.FloatSlider(description="Salary", min=0.0, max=1000.0, value=100.0, step=1.0)
    wdg_taxes = widgets.Checkbox(description="Taxes")
    wdg_tax_slider = widgets.FloatSlider(description="Tax rate", min=0.0, max=1.0, value=0.0, step=0.01)
    
    debug = widgets.Label("Debug")
    
    dashboard.add_widget(wdg_salary_slider, "salary")
    dashboard.add_widget(wdg_tax_slider, "tax")
    
    # Hide tax slider
    wdg_tax_slider.layout.display = "none"
    
    # When tax checkbox is changed
    def taxes_changed(active):
        if(active): # If tax checkbox is set to true
            wdg_tax_slider.layout.display = "flex" # Show tax slider
        else:
            wdg_tax_slider.layout.display = "none" # Hide tax slider
            wdg_tax_slider.value = 0.0 # Set value of tax slider to 0
    
    # Add tax tick box to dashboard and link it to the tax_changed function.
    dashboard.add_widget(wdg_taxes, taxes_changed)
    
    plot = dashboard.add_plot(
        equations=["balance"], 
        names=["Balance"],
        title="Account Balance",
        x_label="Months",
        y_label="Balance",
    )
    main_controls = widgets.VBox([wdg_salary_slider, wdg_taxes, wdg_tax_slider, debug])
    
    
    display(plot)
    display(main_controls)
    
    dashboard.start()



.. parsed-literal::

    Output()



.. parsed-literal::

    VBox(children=(FloatSlider(value=100.0, description='Salary', max=1000.0, step=1.0), Checkbox(value=False, des…


Dynamically update plots
^^^^^^^^^^^^^^^^^^^^^^^^

Plots are managed by the simple dashboard class. Dynamically updating
plots is often required for more advanced features. In this example we
update the number of steps a graph displays.

The dashboard uses the SimpleDashboard.update_plot_data function to
update plot data when the visualization period is selected in a
dropdown.

.. code:: ipython3

    # instantiate dashboard
    dashboard = SimpleDashboard(bptk, scenario_manager="sm", scenario="testScenario")
    
    # Create all widgets
    wdg_months_select = widgets.Dropdown(description="Display", options=["10", "20"])
    
    def month_select(months):
        dashboard.update_plot_data("visualize_to_period", int(months) + 1, -1)
    
    dashboard.add_widget(wdg_months_select, month_select)
    
    plot = dashboard.add_plot(
        equations=["balance"], 
        names=["Balance"],
        title="Account Balance",
        visualize_to_period=11,
        x_label="Months",
        y_label="Balance",
    )
    main_controls = widgets.VBox([wdg_months_select])
    
    
    display(plot)
    display(main_controls)
    
    dashboard.start()



.. parsed-literal::

    Output()



.. parsed-literal::

    VBox(children=(Dropdown(description='Display', options=('10', '20'), value='10'),))


Custom plots
^^^^^^^^^^^^

SimpleDashboard only supports simple plots. More complex plotting
requires custom plots. Below is an example on how to create a custom
table plot.

.. code:: ipython3

    # instantiate dashboard
    dashboard = SimpleDashboard(bptk, scenario_manager="sm", scenario="testScenario")
    
    def custom_plot():
        df = bptk.plot_scenarios(
            scenario_managers=["sm"],
            scenarios=["testScenario"],
            equations=["balance"],
            title="Table Example",
            series_names={"sm_testScenario3_balance": "Balance"},
            return_df=True
        )
    
        display(df)
    
    plot = dashboard.add_custom_plot(custom_plot)
    
    display(plot)
    dashboard.start()



.. parsed-literal::

    Output()


A complex example
~~~~~~~~~~~~~~~~~

This example incorporates all techniques into one model. It is a fairly
complex example that can be used as a reference when creating
interactive dashboard.

First, let’s update the model. This model has an income tax and social
security payments. Social security payments are only paid once a
threshold of 200 is reached. Health insurance is paid optionally, either
based on income or fixed amount. Income now increases over time.

.. code:: ipython3

    from BPTK_Py import sd_functions as sd
    
    # Create the model
    model = Model(starttime=0.0, stoptime=20.0, dt=1.0, name="Test Model")
    
    # The final balance of the account
    stock = model.stock("balance")
    
    # All required flows
    income = model.flow("income_in")
    incomeTax = model.flow("income_tax_in")
    socialSecurity = model.flow("social_security_in")
    
    healthInsurance = model.flow("health_insurance_in")
    healthInsuranceFixed = model.flow("health_insurance_fixed_in") # Health insurance fixed amount
    healthInsuranceIncome = model.flow("health_insurance_income_in") # Health insurance based on income
    
    # All constants (can be adjusted in the interactive dashboard)
    constantSalary = model.constant("salary")
    constantTax = model.constant("income_tax")
    constantSocialSecurity = model.constant("social_security")
    constantHealthInsuranceFixed = model.constant("health_insurance_fixed")
    constantHealthInsuranceIncome = model.constant("health_insurance_income")
    
    constantSalary.equation = 300.0
    constantTax.equation = 0.2
    constantSocialSecurity.equation = 40.0
    constantHealthInsuranceFixed.equation = 0.0
    constantHealthInsuranceIncome.equation = 0.0
    
    # All flow equations
    healthInsuranceIncome.equation = constantHealthInsuranceIncome * constantSalary
    healthInsuranceFixed.equation = constantHealthInsuranceFixed
    
    stock.equation = income - incomeTax - socialSecurity - healthInsurance
    income.equation = constantSalary * sd.lookup(sd.time(), "salary_curve")
    incomeTax.equation = constantSalary * constantTax
    socialSecurity.equation = sd.min(sd.max(0.0, constantSalary - 200.0), 1.0) * constantSocialSecurity
    healthInsurance.equation = healthInsuranceFixed + healthInsuranceIncome
    
    # Create scenario manager and scenario
    scenario_manager = {"sm": {"model": model, 
                "base_points": {
                    "salary_curve":[
                        [1.0, 1.0],
                        [2.0, 1.0],
                        [3.0, 1.0],
                        [4.0, 1.0],
                        [5.0, 1.1],
                        [9.0, 1.20],
                        [13.0, 1.35],
                        [17.0, 1.6],
                    ]
                }}}
    
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager(scenario_manager)
    bptk.register_scenarios(
        scenario_manager="sm",
        scenarios=
        {
            "testScenario2":{
            }
        }
    )

Next, we create the dashboard:

.. code:: ipython3

    from BPTK_Py.visualizations.simple_dashboard import ModelConnection
    
    # instantiate dashboard
    dashboard = SimpleDashboard(bptk, scenario_manager="sm", scenario="testScenario2")
    
    # Create all widgets
    wdg_salary_slider = widgets.FloatSlider(description="Salary", min=0.0, max=1000.0, value=100.0, step=1.0)
    dashboard.add_widget(wdg_salary_slider, "salary")
    
    wdg_tax_slider = widgets.FloatSlider(description="Income Tax", min=0.0, max=1.0, value=0.2, step=0.01)
    dashboard.add_widget(wdg_tax_slider, "income_tax")
    
    wdg_social_security_slider = widgets.FloatSlider(description="Social Security", min=0.0, max=200.0, value=40.0, step=1.0)
    dashboard.add_widget(wdg_social_security_slider, "social_security")
    
    wdg_health_insurance_tick = widgets.Checkbox(description="Health insurance")
    wdg_health_insurance_drop = widgets.Dropdown(description="Type", options=["Fixed rate", "Income dependent"])
    
    wdg_health_insurance_fixed_rate = widgets.FloatSlider(description="Fixed Rate", min=0.0, max=400.0, value=0.0, step=1.0)
    dashboard.add_widget(wdg_health_insurance_fixed_rate, "health_insurance_fixed")
    wdg_health_insurance_income_based = widgets.FloatSlider(description="Percentage", min=0.0, max=1.0, value=0.0, step=0.01)
    dashboard.add_widget(wdg_health_insurance_income_based, "health_insurance_income")
    
    wdg_months_select = widgets.Dropdown(description="Months", options=["10", "20"])
    
    wdg_salary_increase_1 = widgets.FloatSlider(description="Salary 1-4", min=0.0, max=3.0, value=1.0, step=0.01)
    wdg_salary_increase_2 = widgets.FloatSlider(description="Salary 5-9", min=0.0, max=3.0, value=1.1, step=0.01)
    wdg_salary_increase_3 = widgets.FloatSlider(description="Salary 10-13", min=0.0, max=3.0, value=1.2, step=0.01)
    wdg_salary_increase_4 = widgets.FloatSlider(description="Salary 13-17", min=0.0, max=3.0, value=1.35, step=0.01)
    wdg_salary_increase_5 = widgets.FloatSlider(description="Salary 18-20", min=0.0, max=3.0, value=1.6, step=0.01)
    
    # When health insurance is deactivated, the values of wdg_health_insurance_fixed_rate and wdg_health_insurance_income_based are set to 0. These variables save the slider values to restore it if health insurance is enabled again.
    fixed_rate = 0.0
    income_based = 0.0
    
    # Called when health insurance is deactivated or activated
    def health_insurance_event(active):
        global fixed_rate
        global income_based
    
        if(active): # Show widgets
            wdg_health_insurance_drop.layout.display = 'flex'
    
            if(wdg_health_insurance_drop.value == "Fixed rate"): # If the health insurance type is fixed rate
                wdg_health_insurance_fixed_rate.layout.display = 'flex'
                wdg_health_insurance_income_based.layout.display = 'none'
                wdg_health_insurance_fixed_rate.value = fixed_rate # Restore last slider value
            else:  # If the health insurance type is income dependent
                wdg_health_insurance_fixed_rate.layout.display = 'none'
                wdg_health_insurance_income_based.layout.display = 'flex'
                wdg_health_insurance_income_based.value = income_based # Restore last slider value
        else: # Hide widgets
            wdg_health_insurance_drop.layout.display = 'none'
            wdg_health_insurance_fixed_rate.layout.display = 'none'
            wdg_health_insurance_income_based.layout.display = 'none'
    
            # Save last slider value
            if(wdg_health_insurance_drop.value == "Fixed rate"):
                fixed_rate = wdg_health_insurance_fixed_rate.value
            else:
                income_based = wdg_health_insurance_income_based.value
            
            # Set slider values to 0, to remove the effect of health insurance from the model
            wdg_health_insurance_income_based.value = 0.0
            wdg_health_insurance_fixed_rate.value = 0.0
    
    # Called when the type of health insurance is changed
    def health_insurance_type_event(type):
        global fixed_rate
        global income_based
    
        if(type == "Fixed rate"): # If the new type is fixed rate
            # Remove income based slider, save the value and set it to 0
            wdg_health_insurance_income_based.layout.display = 'none'
            income_based = wdg_health_insurance_income_based.value
            wdg_health_insurance_income_based.value = 0.0
            
            # Show fixed rate slider, restore the value
            wdg_health_insurance_fixed_rate.layout.display = 'flex'
            wdg_health_insurance_fixed_rate.value = fixed_rate
    
        else:
            # Remove fixed rate slider, save the value and set it to 0
            wdg_health_insurance_fixed_rate.layout.display = 'none'
            fixed_rate = wdg_health_insurance_fixed_rate.value
            wdg_health_insurance_fixed_rate.value = 0.0
            
            # Show income based slider, restore the value
            wdg_health_insurance_income_based.layout.display = 'flex'
            wdg_health_insurance_income_based.value = income_based
    
    
    def month_select(months):
        dashboard.update_plot_data("visualize_to_period", int(months) + 1, -1)
    
    # Add widgets to the dashboard
    dashboard.add_widget(wdg_health_insurance_tick, health_insurance_event)
    dashboard.add_widget(wdg_health_insurance_drop, health_insurance_type_event)
    dashboard.add_widget(wdg_months_select, month_select)
    dashboard.add_widget(wdg_salary_increase_1, model_connection=ModelConnection(element="salary_curve", points=[0,1,2,3]))
    dashboard.add_widget(wdg_salary_increase_2, model_connection=ModelConnection(element="salary_curve", points=[4]))
    dashboard.add_widget(wdg_salary_increase_3, model_connection=ModelConnection(element="salary_curve", points=[5]))
    dashboard.add_widget(wdg_salary_increase_4, model_connection=ModelConnection(element="salary_curve", points=[6]))
    dashboard.add_widget(wdg_salary_increase_5, model_connection=ModelConnection(element="salary_curve", points=[7]))
    dashboard.add_widget(wdg_months_select, month_select)
    dashboard.add_widget(wdg_months_select, month_select)
    dashboard.add_widget(wdg_months_select, month_select)
    dashboard.add_widget(wdg_months_select, month_select)
    
    # Hide widgets
    wdg_health_insurance_drop.layout.display = 'none'
    wdg_health_insurance_fixed_rate.layout.display = 'none'
    wdg_health_insurance_income_based.layout.display = 'none'
    
    def table():
        df = bptk.plot_scenarios(
            scenario_managers=["sm"],
            scenarios=["testScenario2"],
            equations=["balance", "income_in", "income_tax_in", "social_security_in", "health_insurance_in"],
            title="Table Example",
            series_names={"sm_testScenario2_balance": "Balance", "sm_testScenario2_income_in": "Income", "sm_testScenario2_income_tax_in": "Tax", "sm_testScenario2_social_security_in": "Social Security", "sm_testScenario2_health_insurance_in": "Health Insurance"},
            return_df=True,
            visualize_to_period=int(wdg_months_select.value)+1
        )
    
        display(df)
    
    plot_table = dashboard.add_custom_plot(table)
    
    plot = dashboard.add_plot(
        equations=["balance"], 
        names=["Balance"],
        title="Account Balance",
        visualize_to_period=11,
        x_label="Months",
        y_label="Balance",
    )
    
    tabbed_graphs = widgets.Tab([plot, plot_table])
    tabbed_graphs.set_title(0, "Balance")
    tabbed_graphs.set_title(1, "Table")
    
    main_controls = widgets.VBox([wdg_tax_slider, wdg_social_security_slider, wdg_months_select])
    salary_controls = widgets.VBox([wdg_salary_slider, wdg_salary_increase_1, wdg_salary_increase_2, wdg_salary_increase_3, wdg_salary_increase_4, wdg_salary_increase_5])
    health_insurance_controls = widgets.VBox([wdg_health_insurance_tick, wdg_health_insurance_drop, wdg_health_insurance_fixed_rate, wdg_health_insurance_income_based])
    
    controls_tab = widgets.Tab([main_controls, salary_controls, health_insurance_controls])
    controls_tab.set_title(0, "General")
    controls_tab.set_title(1, "Salary")
    controls_tab.set_title(2, "Health insurance")
    
    display(tabbed_graphs)
    display(controls_tab)
    
    dashboard.start()



.. parsed-literal::

    Tab(children=(Output(), Output()), _titles={'0': 'Balance', '1': 'Table'})



.. parsed-literal::

    Tab(children=(VBox(children=(FloatSlider(value=0.2, description='Income Tax', max=1.0, step=0.01), FloatSlider…



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>Balance</th>
          <th>Income</th>
          <th>Tax</th>
          <th>Social Security</th>
          <th>Health Insurance</th>
        </tr>
        <tr>
          <th>t</th>
          <th></th>
          <th></th>
          <th></th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0.0</th>
          <td>0.0</td>
          <td>100.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>1.0</th>
          <td>80.0</td>
          <td>100.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>2.0</th>
          <td>160.0</td>
          <td>100.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>3.0</th>
          <td>240.0</td>
          <td>100.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>4.0</th>
          <td>320.0</td>
          <td>100.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>5.0</th>
          <td>400.0</td>
          <td>110.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>6.0</th>
          <td>490.0</td>
          <td>112.50</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>7.0</th>
          <td>582.5</td>
          <td>115.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>8.0</th>
          <td>677.5</td>
          <td>117.50</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>9.0</th>
          <td>775.0</td>
          <td>120.00</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
        <tr>
          <th>10.0</th>
          <td>875.0</td>
          <td>123.75</td>
          <td>20.0</td>
          <td>0</td>
          <td>0</td>
        </tr>
      </tbody>
    </table>
    </div>

