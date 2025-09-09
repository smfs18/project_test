import wntr
import wntr.network.controls as controls
#importa a biblioteca do Ant System e do Ant World
from antsys import AntSystem, AntWorld
# Lista de nós (candidatos) para o Ant System.
nodes = []

step = 60 # número de passos por hora (60 passos = 1 hora)
# Criação dos nós (candidatos) para o Ant System.
for node in range(0, 5 * step):
    nodes.append(node / step)
    # print('|'+str(node)+'|'+str(nodes[node])+'|')

# Função que busca a pressão mais alta dentro do intervalo desejado.
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

# Função que busca a pressão mais próxima do valor desejado.
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

# Função de regras que define os caminhos possíveis.
def aco_rules(start, end):
    return [1]

# Função de custo que avalia a qualidade do caminho.
def aco_cost(path):
    wn = wntr.network.read_inpfile("alto_do_ceu_op7.inp") #importa o arquivo de rede
    counter = 0
    # Divide o caminho em três partes iguais.
    first_third = path[0:25]
    second_third = path[25:50]
    third_third = path[50:75]
    # Configuração das válvulas de controle.
    for valve_name, valve in wn.valves():
        # Configuração da válvula 17 (TCV).
        if valve_name == "17" and valve.valve_type == "TCV":
            for i in range(len(first_third)):
                #Define a ação para a válvula.
                action = controls.ControlAction(
                    valve, "setting", first_third[i].start * 5
                )
                #Define a condição para a ocorrência do controle.
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                #Definição do controle.
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                #Adiciona o controle ao arquivo.
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1
        # Configuração da válvula 18 (TCV).
        if valve_name == "18" and valve.valve_type == "TCV":
            for i in range(len(second_third)):
                #Define a ação para a válvula.
                action = controls.ControlAction(
                    valve, "setting", second_third[i].start * 5
                )
                # DDefine a condição para a ocorrência do controle.
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                #Define o controle.
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                #Adicionar o controle ao arquivo.
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1
        #Configuração da válvula 20 (TCV).
        if valve_name == "20" and valve.valve_type == "TCV":
            for i in range(len(third_third)):
                #Define a ação para a válvula.
                action = controls.ControlAction(
                    valve, "setting", third_third[i].start * 5
                )
                # Define a condição para a ocorrência do controle.
                condition = controls.SimTimeCondition(wn, "=", i * 3600)
                # Define o control.
                control = controls.Control(
                    condition,
                    action,
                    name="rule_" + str(counter),
                    priority=controls.ControlPriority.high,
                )
                # Adiciona o controle ao arquivo
                wn.add_control(
                    name="Time_Control_Valve_" + str(valve_name) + "_" + str(counter),
                    control_object=control,
                )
                counter += 1
    # Simulação hidráulica.
    sim = wntr.sim.WNTRSimulator(wn)
    results = sim.run_sim()
    pressure_d = results.node["pressure"]
    # Pressão nos pontos de demanda.
    pressure_at_d16 = pressure_d.loc[:, "D16"]
    pressure_at_d17A = pressure_d.loc[:, "D17A"]
    pressure_at_d17B = pressure_d.loc[:, "D17B"]
    pressure_at_d18 = pressure_d.loc[:, "D18"]
    pressure_at_d21 = pressure_d.loc[:, "D21"]
    #Lista de Controle das configurações de válvulas.
    allControls = list()
    #Congfigurações de válvulas ótimas.
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
    
    # Print organizado - extraindo os dados corretos
    print("\n" + "="*60)
    print("\033[1;36m          CONFIGURAÇÕES DAS VÁLVULAS\033[m")
    print("="*60)
    
    # Horário ótimo
    best_time = bestControls_at_d16[3]["time"]
    best_hour = int(best_time / 3600) if best_time > 0 else 0
    print(f"\n\033[1;33mHorário Ótimo: {best_hour:02d}:00 (Tempo: {best_time}s)\033[m")
    
    print(f"\n\033[1;32mConfigurações das Válvulas:\033[m")
    
    # Extrair configurações das válvulas
    if bestControls_at_d16[0] is not None:
        action = bestControls_at_d16[0]['then_actions'][0]
        setting = float(action.split('IS ')[1])
        print(f"\033[34mVálvula 17: {setting:.2f}\033[m")
    
    if bestControls_at_d16[1] is not None:
        action = bestControls_at_d16[1]['then_actions'][0] 
        setting = float(action.split('IS ')[1])
        print(f"\033[34mVálvula 18: {setting:.2f}\033[m")
    
    if bestControls_at_d16[2] is not None:
        action = bestControls_at_d16[2]['then_actions'][0]
        setting = float(action.split('IS ')[1]) 
        print(f"\033[34mVálvula 20: {setting:.2f}\033[m")
    
    print("\n" + "="*60)
    print("\033[1;36m          PRESSÕES NOS DISTRITOS\033[m")  
    print("="*60)
    
    # Apenas as pressões de cada distrito
    print(f"\n\033[32mDistrito D16: {bestControls_at_d16[3]['pressure']:.2f} bar\033[m")
    print(f"\033[34mDistrito D17A: {bestControls_at_d17A[3]['pressure']:.2f} bar\033[m")
    print(f"\033[34mDistrito D17B: {bestControls_at_d17B[3]['pressure']:.2f} bar\033[m")
    print(f"\033[34mDistrito D18: {bestControls_at_d18[3]['pressure']:.2f} bar\033[m")
    print(f"\033[34mDistrito D21: {bestControls_at_d21[3]['pressure']:.2f} bar\033[m")
    
    print("="*60)
    
    allControls.append(["D16", bestControls_at_d16])
    allControls.append(["D17A", bestControls_at_d17A])
    allControls.append(["D17B", bestControls_at_d17B])
    allControls.append(["D18", bestControls_at_d18])
    allControls.append(["D21", bestControls_at_d21])

    return allControls

# Função heurística que retorna o valor da informação do candidato.
def aco_heuristic(path, candidate):
    return candidate.info


new_world = AntWorld(nodes, aco_rules, aco_cost, aco_heuristic)
# Criação do mundo com as regras, custo e heurística definidas.
ant_opt = AntSystem(world=new_world, n_ants=100)
# Aumento no número de iterações e formigas para melhorar a busca.
ant_opt.optimize(200, 40)