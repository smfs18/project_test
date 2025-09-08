import wntr
import wntr.network.controls as controls

from antsys import AntSystem, AntWorld

nodes = []

step = 60
for node in range(0, 5 * step):
    nodes.append(node / step)
    # print('|'+str(node)+'|'+str(nodes[node])+'|')


def generate_controls(valve, wn, min_pressure, max_pressure):
    pressures = dict(valve)
    new_pressure = 0.0
    new_key = 0.0
    wn_dict = wntr.network.to_dict(wn)
    ta_na_faixa = False

    count = 0

    counterBest = 0
    bestControls = []

    for key, value in pressures.items():
        if value >= min_pressure and value <= max_pressure:
            ta_na_faixa = True
            if value > new_pressure:
                counterBest = count
                new_pressure = value
                new_key = key
        count += 1

    if ta_na_faixa is not True:
        bestControls.append(None)
        bestControls.append(None)
        bestControls.append(None)
        bestControls.append({"pressure": new_pressure, "time": new_key})
        return bestControls

    count = 0
    for item in wn_dict["controls"]:
        if count == counterBest:
            bestControls.append(item)
        count += 1
        if count == 25:
            count = 0

    bestControls.append({"pressure": new_pressure, "time": new_key})
    return bestControls


def search_pressure(valve, hour, wn, min_pressure, max_pressure):
    pressures = dict(valve)
    wn_dict = wntr.network.to_dict(wn)
    ta_na_faixa = False

    new_pressure = 0.0
    count = 0

    counterBest = 0
    bestControls = []
    print(valve)
    for key, value in pressures.items():
        if key == hour:
            if value >= min_pressure and value <= max_pressure:
                ta_na_faixa = True
                new_pressure = value
                if key == 0:
                    count = 0
                else:
                    count = int(int(key) / 3600)

    if ta_na_faixa is not True:
        bestControls.append(None)
        bestControls.append(None)
        bestControls.append(None)
        bestControls.append({"pressure": new_pressure, "time": hour})
        return bestControls

    for item in wn_dict["controls"]:
        if count == counterBest:
            bestControls.append(item)
        counterBest += 1
        if counterBest == 25:
            counterBest = 0

    bestControls.append({"pressure": new_pressure, "time": hour})
    return bestControls


def aco_rules(start, end):
    return [1]


def aco_cost(path):
    wn = wntr.network.read_inpfile("alto_do_ceu_op7.inp")
    counter = 0

    first_third = path[0:25]
    second_third = path[25:50]
    third_third = path[50:75]

    for valve_name, valve in wn.valves():
        if valve_name == "17" and valve.valve_type == "TCV":
            for i in range(len(first_third)):
                # Define an action for the valve
                action = controls.ControlAction(
                    valve, "setting", first_third[i].start * 5
                )
                # Define a condition for the ocurrence of the control
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                # Define the Control
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                # Add the control to the file
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1

        if valve_name == "18" and valve.valve_type == "TCV":
            for i in range(len(second_third)):
                # Define an action for the valve
                action = controls.ControlAction(
                    valve, "setting", second_third[i].start * 5
                )
                # Define a condition for the ocurrence of the control
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                # Define the Control
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                # Add the control to the file
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1

        if valve_name == "20" and valve.valve_type == "TCV":
            for i in range(len(third_third)):
                # Define an action for the valve
                action = controls.ControlAction(
                    valve, "setting", third_third[i].start * 5
                )
                # Define a condition for the ocurrence of the control
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                # Define the Control
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                # Add the control to the file
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1

    sim = wntr.sim.WNTRSimulator(wn)
    results = sim.run_sim()
    pressure_d = results.node["pressure"]

    pressure_at_d16 = pressure_d.loc[:, "D16"]
    pressure_at_d17A = pressure_d.loc[:, "D17A"]
    pressure_at_d17B = pressure_d.loc[:, "D17B"]
    pressure_at_d18 = pressure_d.loc[:, "D18"]
    pressure_at_d21 = pressure_d.loc[:, "D21"]

    allControls = list()

    bestControls_at_d16 = generate_controls(pressure_at_d16, wn, 10.0, 18.0)
    bestControls_at_d17A = search_pressure(
        pressure_at_d17A,
        bestControls_at_d16[3]["time"],
        wn,
        17.0,
        30.0,
    )
    bestControls_at_d17B = search_pressure(
        pressure_at_d17B,
        bestControls_at_d16[3]["time"],
        wn,
        17.0,
        30.0,
    )
    bestControls_at_d18 = search_pressure(
        pressure_at_d18,
        bestControls_at_d16[3]["time"],
        wn,
        12.0,
        24.0,
    )
    bestControls_at_d21 = search_pressure(
        pressure_at_d21,
        bestControls_at_d16[3]["time"],
        wn,
        10.0,
        18.0,
    )

    print("\033[m----------- [ best controls ] -----------")
    print("\033[32m{}\033[m".format(bestControls_at_d16))
    print("- - - - - - - - - - - - - - - - - - - - - - -")
    print("\033[34m{}\033[m".format(bestControls_at_d17A))
    print("- - - - - - - - - - - - - - - - - - - - - - -")
    print("\033[34m{}\033[m".format(bestControls_at_d17B))
    print("- - - - - - - - - - - - - - - - - - - - - - -")
    print("\033[34m{}\033[m".format(bestControls_at_d18))
    print("- - - - - - - - - - - - - - - - - - - - - - -")
    print("\033[34m{}\033[m".format(bestControls_at_d21))
    print("\033[m----------- [ best controls ] -----------")

    allControls.append(["D16", bestControls_at_d16])
    allControls.append(["D17A", bestControls_at_d17A])
    allControls.append(["D17B", bestControls_at_d17B])
    allControls.append(["D18", bestControls_at_d18])
    allControls.append(["D21", bestControls_at_d21])

    return allControls


def aco_heuristic(path, candidate):
    return candidate.info


new_world = AntWorld(nodes, aco_rules, aco_cost, aco_heuristic)

ant_opt = AntSystem(world=new_world, n_ants=100)

ant_opt.optimize(200, 40)