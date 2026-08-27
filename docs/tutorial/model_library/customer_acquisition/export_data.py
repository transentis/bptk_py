import marimo

__generated_with = "0.23.13"
app = marimo.App()


@app.cell
def _():
    # start bptk-py
    from BPTK_Py.bptk import bptk 
    bptk = bptk()
    bptk.register_scenarios(scenario_manager="smCustomerAcquisition",scenarios={
                              "interactiveScenario":{
                                  "constants":{
                                     "referrals":0,
                                      "advertisingSuccessPct":0.1,
                                      "referralFreeMonths":3,
                                      "referralProgamAdoptionPct":10
                                    }
                              }
    }

    )
    return (bptk,)


@app.cell
def _(bptk):
    bptk.list_scenarios(["smCustomerAcquisition"])
    return


@app.cell
def _(bptk):
    # magic command not supported in marimo; please file an issue to add support
    # %%time

    ## save the file in the current working directory
    import os
    export_directory=os.path.join(os.getcwd(),"export")
    if not os.path.isdir(export_directory):
        os.mkdir(export_directory)
    export_filename= os.path.join(export_directory,"customer_aquisition.xlsx")

    ## Load the BPTK Package
    bptk.export_scenarios(
        scenario_manager="smCustomerAcquisition",
        equations=["customers","profit"],
        filename=export_filename,
        interactive_scenario="interactiveScenario",
        interactive_equations=["customers","profit"],
        interactive_settings= {
            "advertisingSuccessPct":(0,0.2,0.01),
            "referralFreeMonths":(2,5,1),
            "referralProgramAdoptionPct":(0,31,1),
            "referrals":(2,5,1)
        }
    )
    return


if __name__ == "__main__":
    app.run()
