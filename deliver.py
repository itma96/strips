import sys
import pickle
import math
from itertools import combinations
from copy import copy, deepcopy

from Lab05 import make_var, make_const, make_atom, make_or, make_and, make_neg, \
                is_variable, is_constant, is_atom, is_function_call, \
                print_formula, get_args, get_head, get_name, get_value ,\
                unify, substitute
from Lab06 import add_statement, is_positive_literal, is_negative_literal, \
                make_unique_var_names
                
NAME = 0
ARGS = 1
PRECONDS = 2
N_EFFECTS = 3
P_EFFECTS = 4
UNCHANGED = 5

def compute_cost(plan):
    cost = 0
    for action in plan:
        if action[NAME] == "Fly":
            start = get_value(action[ARGS][0])
            stop = get_value(action[ARGS][1])          
            distance = math.sqrt(sum([(a - b) ** 2 for a, b in zip(start, stop)]))
            cost += distance
    return cost

def print_plan(plan):
    print " ".join([print_action(action, True) for action in plan])

def print_state(state):
    print("State now:")
    for s in state:
        print("\t" + print_formula(s, True))

def print_action(action, return_result=False):
    ret = ""
    if action[NAME] == "Fly":
        ret += "Fly" + "(" + " ".join([print_formula(arg, True) for arg in action[ARGS]]) + ")"
    if action[NAME] == "Load":
        ret += "Load" + "(" + print_formula(action[ARGS][1], True) + ")"
    if action[NAME] == "Deliver":
        ret += "Deliver" + "(" + print_formula(action[ARGS][1], True) + ")"
    if return_result:
        return ret
    print(ret)
    return

def print_kb(kb):
    print "#################################################################################"
    print("KB now:")
    for key in kb:
        print(key + ":")
        if key == 'init':
            for fact in kb['init']:
                print("\t" + print_formula(fact, True))
        if key == 'world':
            for fact in kb['world']:
                print("\t" + print_formula(fact, True))    
        if key == 'goal':
            for fact in kb['goal']:
                print("\t" + print_formula(fact, True))
        if key == 'actions':
            for action in kb['actions']:
                    print("\t" + action[NAME] + "(" + " ".join([print_formula(arg, True) for arg in action[ARGS]]) + "):" +
                           "\n\t\t" + " ".join([print_formula(precond, True) for precond in action[PRECONDS]]) +
                           "\n\t\t" + " ".join([print_formula(effect, True) for effect in action[N_EFFECTS]]) +
                           "\n\t\t" + " ".join([print_formula(effect, True) for effect in action[P_EFFECTS]]) +
                           "\n\t\t" + " ".join([print_formula(effect, True) for effect in action[UNCHANGED]]))       
    print "#################################################################################"               
                         
def make_plan(scenario):

    print scenario
    N, N = scenario['dimensions']
    map = [(i, j) for i in range(N) for j in range(N)]

    kb = {}

    # add initial state facts
    kb['init'] = []

    # add drone's initial position
    add_statement(kb['init'], make_atom("Position", make_const(scenario['initial_position'])))

    # compartment empty
    add_statement(kb['init'], make_atom("Empty"))

    # add 'world' state facts
    kb['world'] = []

    # add warehouses
    warehouses = scenario['warehouses']
    for warehouse in warehouses:
        add_statement(kb['world'], make_atom("Warehouse", make_const(warehouse)))

    # add products
    products = range(scenario['number_of_products'])

    # add available products
    for warehouse, product in scenario['available_products']:
        add_statement(kb['world'], make_atom("hasProduct", make_const(warehouse),
                                            make_const(product)))

    # add clients
    clients = scenario['clients']
    for client in clients:
        add_statement(kb['world'], make_atom("Client", make_const(client)))

    # add orders
    orders = scenario['orders']
    for client, product in orders:
        add_statement(kb['world'], make_atom("Order", make_const(client),
                                            make_const(product)))

    # add goal facts
    kb['goal'] = []

    # orders delivered
    for order in orders:
        add_statement(kb['goal'], make_atom("Delivered", make_const(order[0]), make_const(order[1])))
        
    # drone's position    
    add_statement(kb['goal'], make_atom("Position", make_const(clients[-1])))       
    
    # compartment empty    
    add_statement(kb['goal'], make_atom("Empty"))   

    # add actions
    kb['actions'] = []
    
    # add deliver actions
    for (cell, product) in scenario['orders']:
        kb['actions'].append(("Deliver", [make_const(cell), make_const(product)], [make_atom("Carries", make_const(product)),
            make_atom("Position", make_const(cell)),
            make_atom("Client", make_const(cell)),
            make_atom("Order", make_const(cell), make_const(product))], 
            [make_atom("Carries", make_const(product))], [make_atom("Delivered", make_const(cell), make_const(product)),
            make_atom("Empty")], [make_atom("Position", make_const(cell)), make_atom("Client", make_const(cell)), 
            make_atom("Order", make_const(cell), make_const(product))]))
               
    # add load actions
    for (warehouse, product) in scenario['available_products']:
        kb['actions'].append(("Load", [make_const(warehouse), make_const(product)], [make_atom("Position", make_const(warehouse)),
            make_atom("Warehouse", make_const(warehouse)),
            make_atom("hasProduct", make_const(warehouse), make_const(product)),
            make_atom("Empty")], [make_atom("Empty")], [make_atom("Carries", make_const(product))], 
            [make_atom("Position", make_const(warehouse)), make_atom("Warehouse", make_const(warehouse)), 
            make_atom("hasProduct", make_const(warehouse), make_const(product))]))         
    
    # add fly actions
    for start, stop in list(combinations(scenario['warehouses'] + scenario['clients'], 2)):
        kb['actions'].append(("Fly", [make_const(start), make_const(stop)], [make_atom("Position", make_const(start))
            ], [make_atom("Position", make_const(start))], [make_atom("Position", make_const(stop))], []))

        kb['actions'].append(("Fly", [make_const(stop), make_const(start)], [make_atom("Position", make_const(stop))
            ], [make_atom("Position", make_const(stop))], [make_atom("Position", make_const(start))], []))            
        
    for stop in scenario['warehouses']:
        kb['actions'].append(("Fly", [make_const(scenario['initial_position']), make_const(stop)], [make_atom("Position", 
        make_const(scenario['initial_position']))], [make_atom("Position", make_const(scenario['initial_position']))], 
        [make_atom("Position", make_const(stop))], []))  

        kb['actions'].append(("Fly", [make_const(stop), make_const(scenario['initial_position'])], 
        [make_atom("Position", make_const(stop))], [make_atom("Position", make_const(stop))], 
        [make_atom("Position", make_const(scenario['initial_position']))], []))          

    print_kb(kb)

    res = backward_search(kb['goal'], [], kb)
    return res

# PA BACKWARD   
def reached_init_state(state, init_state):
    for fact in init_state:
        if fact not in state:
            return False
    return True
    
def applicable_actions(state, kb, last_applied):
    applicable_actions = []
    full_state = state + kb['world'] 
    for action in kb['actions']:   
        if last_applied != None and action[NAME] == last_applied:
            continue
        
        ok = True
        
        for i in action[N_EFFECTS]:
            if i in full_state:
                ok = False
                break
        if not ok:
            continue
        for i in action[P_EFFECTS]:
            if i not in full_state:
                ok = False
                break
        if not ok:
            continue
        for i in action[UNCHANGED]:
            if i not in full_state:
                ok = False
                break
                
        if ok:
            applicable_actions.append(action)
        
    return applicable_actions    
    
def apply_action(action, state, path, kb):
    #print "apply_action " + print_action(action, True)
    new_state = deepcopy(state)
    for precond in action[PRECONDS]:
        if precond not in kb['world'] and precond not in new_state:
            new_state.append(precond)
    for effect in action[N_EFFECTS]:
        if effect not in kb['world'] and effect not in new_state:
            new_state.append(effect)
    for effect in action[P_EFFECTS]:
        if effect not in kb['world'] and effect in new_state:
            new_state.remove(effect)
    res = backward_search(new_state, [action] + path, kb, action[NAME])
    return res
     
def backward_search(state, path, kb, last_applied = None):
    #print "backward_search(" + str(state) + ", " + str(path) + ", " + str(last_applied) + ")"
        
    actions = applicable_actions(state, kb, last_applied)
        
    for action in actions:
        res = apply_action(action, state, path, kb)
        if res != None:
            return res
            
    if reached_init_state(state, kb['init']):
        return path            
                
    return None       

    
def main(args):
    scenario = pickle.load(open('scenario6.pkl'))

    plan = make_plan(scenario)
    
    print 'cost plan: ' + str(compute_cost(plan))

    print_plan(plan)

if __name__ == '__main__':
    main(sys.argv)
