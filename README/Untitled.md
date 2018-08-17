

```python
from BPTK_Py.bptk import bptk
bptk = bptk()
bptk.plot_scenarios(
    scenario_managers=["smSimpleProjectManagement"],
    scenarios=["scenario80"],
    equations=['openTasks',"closedTasks"],
    title="Example Graph\n",
    x_label="Time",
    kind="area",
    y_label="Some Number",
    start_date="1/11/2017",
    freq="D",
    series_names={"openTasks":"open  Tasks","closedTasks" : "Closed Tasks"}
)
```


![png](output_0_0.png)

