# ToM-discrepancy-resolution
Project for enabling agents to use their Theory of Mind to resolve discrepancies pertaining to plan validity by communicating and/or acting in the environment.

If you use this code in your research, please consider using the following reference:

```shell
@inproceedings{shvo-klas-mci-icaps-discres2022,
  author    = {Shvo, Maayan and Klassen, Toryn Q and McIlraith, Sheila A},
  title		= {Resolving Misconceptions about the Plans of Agents via {T}heory of {M}ind},
  booktitle = "Proceedings of the Thirty-Second International Conference on
                Automated Planning and Scheduling (ICAPS 2022)",
  pages=    {719-729},
  year     = {2022}
}


```

## Platform
Tested on Ubuntu 20.04


## Dependencies
* [The Fast Downward planning system](https://www.fast-downward.org/ObtainingAndRunningFastDownward). We assume that Fast Downward has been correctly installed prior to using the code in this repository.  
* [SymPy](https://www.sympy.org/en/index.html) - a Python library for symbolic mathematics. 
* The files in the `pdkb` directory (under the `discrepancy_resolution` directory) are taken from the [pdkb-planning repository underlying the epistemic planner RP-MEP](https://github.com/QuMuLab/pdkb-planning).


## Run

To run, `disc_res.py` (located in the `discrepancy_resolution` directory) expects as input a problem file written in the PDKBDDL file format, a file containing a plan, and a file containing a tuple of agents, with a single agent per line:

```shell
python discrepancy_resolution/disc_res.py <pdkbddl problem file> <plan file> <agent tuple file>
```
For example, the following uses the corridor domain:
```shell
python discrepancy_resolution/disc_res.py domains/corridor/prob.pdkbddl domains/corridor/plan.txt domains/corridor/agent_tuple.txt
```
and will output a valid discrepancy resolving plan. 

* See [domains/corridor/plan.txt](domains/corridor/plan.txt) and [domains/corridor/agent_tuple.txt](domains/corridor/agent_tuple.txt) for examples of the correct way to format the plan and agent tuple files expected by disc_res.py. In general, the plan file should contain a single action per line, where the action uses the following format: <name_of_action>\_<agent_ID>\_<action_specific_args> (e.g., share_a_a_l1 where share is the name of the action, a is the agent ID, and a and l1 are actions specific arguments). The agent tuple file should contain a single agent ID per line, where agent IDs are specified in the domain file (e.g., [domains/corridor/domain.pdkbddl](domains/corridor/domain.pdkbddl)).
* Note that the value of the global variable FD_PATH in `disc_res.py` must be changed to correspond to the installation location of Fast Downward on your machine.
