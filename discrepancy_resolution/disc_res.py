import os, sys, time, pickle

from pdkb.actions import *
from pdkb.problems import *
from pdkb.rml import parse_rml, Literal
from pdkb.kd45 import PDKB, project
from pdkb.pddl.grounder import GroundProblem
from pdkb.test.utils import read_file, write_file, run_command, parse_output_ipc

from sympy.logic.boolalg import Not, And, Or
from sympy.abc import x, A, B, C, D, E, F, G
from sympy.logic.boolalg import to_dnf

# replace PATH_TO_FD_INSTALLATION with the path to fast-downward.py
FD_PATH = "PATH_TO_FD_INSTALLATION"

def generate_validity_formula(problem,agent_tuple,plan_file):

	stringified_plan_for_regression = []

	curr_state_file = open(plan_file,'r')
	raw_lines = curr_state_file.readlines()
	plan_for_regression = [line.strip() for line in raw_lines if line.strip().find(";") == -1]
	

	for action in plan_for_regression:
		stringified_plan_for_regression.append(str(action))

	stringified_plan_for_regression.reverse()

	all_effects = []
	all_pres = []

	precond_reg_conditions = set()

	agent_tuple_string = ""
	for agent in agent_tuple:
		agent_tuple_string += "B{0}_".format(agent)

	goal_rml_dict = {}
	for goal_rml in list(problem.goal.rmls):
		goal_rml_dict[goal_rml] = []

	# print("GOAL: " + str([rml.pddl() for rml in list(problem.goal.rmls)]))

	goal_rml_matches_in_effects_of_cond_effects = []

	conditions_of_effects_that_satisfy_positive_goal_components = []
	conditions_of_effects_that_satisfy_negated_goal_components = []

	# go over every action in the reversed plan
	for act1 in stringified_plan_for_regression:
		for act2 in problem.domain.actions:

			# we do this in order to get all the action's data structures (preconds, cond effs)
			if act2.name.lower().strip() == act1.lower().strip(): 
				
				# this gives us all the conditional effects of the current action
				for ef in act2.effs:
					for e in list(ef[0]):
						
						all_effects.append(str(e.eff).lower())

				pln_idx = stringified_plan_for_regression.index(act1)
				temp_effects = []

				# since we start from the last action, we go over all the actions
				# preceding the current action in the plan and 
				# we add all of their conditional effects to a list called temp_effects
				for act3 in stringified_plan_for_regression[pln_idx + 1:]:
					for act4 in problem.domain.actions:
						if act4.name.lower() == act3.lower():
							for ef in act4.effs:
								for e in list(ef[0]):
									temp_effects.append(str(e.eff).lower())


				for ef2 in act2.effs:
					for e2 in list(ef2[0]):
						for goal_rml in list(problem.goal.rmls):
							if str(goal_rml.pddl()).lower() == str(e2.eff.pddl()).lower():
								# If this condition is satisfied, that means that there are effects 
								# of conditional effects of the current action that satisfy part of the goal
								# so we add the conditions of these to a special list and ask later (as we do)
								# if any of the effects of the conditional effects of the other actions
								# satisfy the conditions in question. if they do, then they get added to a 
								# special list and so on. whatever conditions in this special list are 
								# not satisfied by any effects of any preceding actions, those conditions
								# are then added to regression formula

								# we also add the conditions that we find to the goal_rml_dict
								# then, we will have a dict with the keys being the goal components
								# and the values being the conditions that must hold true in the initial state
								# in order for that component of the goal to be satisfied
								# if there is more than one entry in the list (the value) then that means
								# that the goal component in question can be satisfied in more than one way
								# this means a disjunction so we do something with that

								# we need to get this:
								# not(at(c,l1)) and not(at(c,l2)) and not(at(c,l3))
								# AND
								# at(b,l1) or at(b,l2) or at(b,l3)

								# in DNF form:
								# at(b,l1) and not(at(c,l1)) and not(at(c,l2)) and not(at(c,l3))
								# OR 
								# at(b,l2) and not(at(c,l1)) and not(at(c,l2)) and not(at(c,l3))
								# OR
								# at(b,l3) and not(at(c,l1)) and not(at(c,l2)) and not(at(c,l3))

								# the top row will come from going over the goal components that are 
								# ***negated**. it's all the NEGATIONS OF conditions that must hold (the negations, that is)
								#  in the initial state so that we ensure that the goal is satisfied
								#  if even one of these negated conditions holds in the initial state, 
								#  then the goal will not be satisfied. so we will get a disjunction here

								#  for the second line, we will get multiple elements in the list
								#  in the value of the goal component. we only need one of these conditions to hold in 
								#  the initial state in order to satisfy that component of the goal (and we don't care which one)
								#     so this means a disjunction
								

								conditions_of_effects_that_satisfy_positive_goal_components.append(list(e2.condp.rmls))

								# for cond in list(e2.condp.rmls):
								#     conditions_of_effects_that_satisfy_positive_goal_components.append(str(cond))

						for goal_rml in list(problem.goal.rmls):
							if str(goal_rml.negate().pddl()).lower() == str(e2.eff.pddl()).lower():
								# If this condition is satisfied, that means that there are effects 
								# of conditional effects of the current action that satisfy A NEGATION of 
								# part of the goal. THIS IS UNDESIRABLE so we add the negation of the 
								# conditions of these to the regression formula. a more complete version of this
								# also adds the negated conditions to a special list and ask later (as we do)
								# if any of the effects of the conditional effects of the other actions
								# satisfy the (negated) conditions in question. if they do, then they get added to a 
								# special list and so on. whatever conditions in this special list are 
								# not satisfied by any effects of any preceding actions, the negation of
								# those conditions is then added to regression formula

								conditions_of_effects_that_satisfy_negated_goal_components.append(list(e2.condp.rmls))
								


				# print("conditions_of_effects_that_satisfy_positive_goal_components:" + str(conditions_of_effects_that_satisfy_positive_goal_components))
				# print("conditions_of_effects_that_satisfy_negated_goal_components:" + str(conditions_of_effects_that_satisfy_negated_goal_components))
				

				# now we go over the conditions of the conditional effects of the current action 
				# and we ask whether the condition appears in the effects of the actions preceding the current 
				# action in the plan. if THE CONDITION DOES NOT APPEAR IN ANY OF THE PREVIOUS ACTIONS' EFFECTS
				# then the condition needs to be added to the regression formula since that means it must hold
				# in the initial state, otherwise the goal will not be satisfied
				for ef2 in act2.effs:
					for e2 in list(ef2[0]):
						for cond in list(e2.condp.rmls):
							if cond not in temp_effects:
								if str(cond).lower() in all_pres: 
									precond_reg_conditions.add(str(cond))

						for cond in list(e2.condn.rmls):
							if cond not in temp_effects:
								if str(cond).lower() in all_pres:
									precond_reg_conditions.add(str(cond))
						

				# go over preconditions

				for pre in list(act2.pre.rmls):
					if pre not in temp_effects and pre.pddl().find("B{0}".format(agent_tuple_string[1])) == -1 and pre.pddl().find("P{0}".format(agent_tuple_string[1])) == -1:
						# print(print(pre.pddl()))
						precond_reg_conditions.add(str(pre.pddl()))
						all_pres.append(str(pre.pddl()))

				for pre in list(act2.npre.rmls):
					temp_npre = "!" + str(pre.pddl())
					if temp_npre not in temp_effects:
						precond_reg_conditions.add(temp_npre)
						all_pres.append(temp_npre)

				# now we construct the regression formula

				# print(precond_reg_conditions)

				regression_formula = "Or("
				disjuncts = []
				for i, cond in enumerate(list(conditions_of_effects_that_satisfy_positive_goal_components)):
					
					regression_formula += "And({0}, ".format("And(" + str(cond)[1:-1] + ")")
					for condd in list(conditions_of_effects_that_satisfy_negated_goal_components):
						
						regression_formula += " {0},".format("Not(And(" + str(condd)[1:-1] + "))")

					for precond in list(precond_reg_conditions):

						regression_formula += " {0},".format("And(" + str(precond) + ")")

					regression_formula = regression_formula[:-1]
					regression_formula += "), "
					
				regression_formula += ")"

				regression_formula = regression_formula.replace("!","~")

				# print("REGRESSION FORMULA IS: {0}".format(regression_formula))

				# first simplify the regression formula we found
				simplified_valid_formula_in_dnf = to_dnf(regression_formula,simplify=True)
				
				# then convert its negation to DNF
				simplified_negated_valid_formula_in_dnf = to_dnf(Not(simplified_valid_formula_in_dnf),simplify=True)

				# print(str(simplified_valid_formula_in_dnf))

				
				# print(simplified_negated_valid_formula_in_dnf)  

				all_disjuncts_of_val_formula = []
				all_disjuncts_of_negated_val_formula = []

				

				disc_res_action_template = "(:action discResSpecialAction<template_action_num> :precondition (and (dummy)) :effect (and (when (and <CONJUNCTION_FORMULA>) (discResGoal) ) ) )"

				for i, disjunct in enumerate( str(simplified_valid_formula_in_dnf).split('|')): # + str(simplified_negated_valid_formula_in_dnf).split('|')
					condition_for_special_action = ""

					for conjunct in disjunct.replace('(','').replace(')','').split('&'):
						
						if conjunct.find("~") != -1:
							if conjunct.find("Ba_") == -1 and conjunct.find("Pa_") == -1:
								
								condition_for_special_action += "({0}not_".format(agent_tuple_string) + conjunct.replace("~","").replace(" ","") + ") "
							else:
								condition_for_special_action += "(not_" + conjunct.replace("~","").replace(" ","") + ") "
							condition_for_special_action += "(not_" + conjunct.replace("~","").replace(" ","") + ") "
						else:
							if conjunct.find("Ba_") == -1 and conjunct.find("Pa_") == -1:

								condition_for_special_action += "({0}".format(agent_tuple_string) + conjunct.replace("~","").replace(" ","") + ") "
							else:
								condition_for_special_action += "(" + conjunct.replace("~","").replace(" ","") + ") "
							condition_for_special_action += "(" + conjunct.replace("~","").replace(" ","") + ") "
					temp_disc_res_action_template = disc_res_action_template.replace('<CONJUNCTION_FORMULA>',condition_for_special_action).replace('<template_action_num>',str(i+1))

					all_disjuncts_of_val_formula.append(condition_for_special_action)
					

				disc_res_action_template = "(:action discResNEGATIONSpecialAction<template_action_num> :precondition (and (dummy)) :effect (and (when (and <CONJUNCTION_FORMULA>) (discResGoalNEGATION) ) ) )"
				for i, disjunct in enumerate(str(simplified_negated_valid_formula_in_dnf).split('|')):
					condition_for_special_action = ""

					for conjunct in disjunct.replace('(','').replace(')','').split('&'):
						if conjunct.find("~") != -1:
							if conjunct.find("Ba_") == -1 and conjunct.find("Pa_") == -1:
								condition_for_special_action += "({0}not_".format(agent_tuple_string) + conjunct.replace("~","").replace(" ","") + ") "
							else:
								condition_for_special_action += "(not_" + conjunct.replace("~","").replace(" ","") + ") "
								
							condition_for_special_action += "(not_" + conjunct.replace("~","").replace(" ","") + ") "
						else:
							if conjunct.find("Ba_") == -1 and conjunct.find("Pa_") == -1:
								condition_for_special_action += "({0}".format(agent_tuple_string) + conjunct.replace("~","").replace(" ","") + ") "
							else:
								condition_for_special_action += "(" + conjunct.replace("~","").replace(" ","") + ") "
							
							condition_for_special_action += "(" + conjunct.replace("~","").replace(" ","") + ") "
					temp_disc_res_action_template = disc_res_action_template.replace('<CONJUNCTION_FORMULA>',condition_for_special_action).replace('<template_action_num>',str(i+1))

					all_disjuncts_of_negated_val_formula.append(condition_for_special_action)


				

	# print("Regression conditions:")
	# print(precond_reg_conditions)
	list_reg_formula = list(precond_reg_conditions)
	reg_formula_file = open('reg_formula.txt','w')
	for pred in list_reg_formula:
		reg_formula_file.write(str(pred)+"\n")

	reg_formula_file.close()

	return [all_disjuncts_of_val_formula, all_disjuncts_of_negated_val_formula]


def run_planner(disc_res_goal):

	problem_file = open("pdkb-problem_modified_goal.pddl", "w")
	orig_pddl_problem_file = open("pdkb-problem.pddl", "r")
		
	raw_lines = orig_pddl_problem_file.readlines()
	lines = [line.strip() for line in raw_lines]

	goal_flag = False

	for line in lines:
		if line.find("(:goal") != -1:
			goal_flag = True
			problem_file.write("(:goal (and " + disc_res_goal)
			problem_file.write('\n')
			continue

		if goal_flag and line.find("))") != -1:
			goal_flag = False

		if not goal_flag:
			problem_file.write(line)
			problem_file.write('\n')

	problem_file.close()

	os.system("{0} pdkb-domain.pddl pdkb-problem_modified_goal.pddl --search 'astar(hmax())' > FD_output.txt".format(FD_PATH))



def parse_plan():
	f = open("sas_plan")

	raw_lines = f.readlines()
	lines = [line.strip() for line in raw_lines]

	print("=== Discrepancy resolving plan ===")

	for line in lines:
		if line.find(";") == -1:
			print(line)


def formulate_discrepancy_resolution_goal(disjuncts_of_val_formula_and_negated_val_formula,agent_tuple):
	template_disjunctive_disc_res_goal = "(or (and <DNF> (not <NEGATED_DNF>)) (and (not <DNF>) <NEGATED_DNF>) )"
	first_agent_in_tuple = agent_tuple[0]

	# if we want to use special disc res actions then this will be the XOR goal
	# return "(or (and (disc_resolution) (not (disc_resolution_two))) (and (not (disc_resolution)) (disc_resolution_two)) )"

	# otherwise, we formulate the goal using the disjuncts
	disjuncts_of_DNF = "(or "
	for disjunct in disjuncts_of_val_formula_and_negated_val_formula[0]:
		disjuncts_of_DNF += "(and "
		disjuncts_of_DNF += disjunct + " "
		disjuncts_of_DNF += ")"
	disjuncts_of_DNF += ")"

	disjuncts_of_negated_DNF = "(or "
	for disjunct in disjuncts_of_val_formula_and_negated_val_formula[1]:
		disjuncts_of_negated_DNF += "(and "
		disjuncts_of_negated_DNF += disjunct + " "
		disjuncts_of_negated_DNF += ")"
	disjuncts_of_negated_DNF += ")"

	disc_res_goal = template_disjunctive_disc_res_goal.replace("<DNF>", disjuncts_of_DNF).replace("<NEGATED_DNF>",disjuncts_of_negated_DNF)
	
	# print(disc_res_goal) #.replace("not_B{0}".format(first_agent_in_tuple),"P{0}".format(first_agent_in_tuple)).replace("not_P{0}".format(first_agent_in_tuple),"B{0}_not".format(first_agent_in_tuple)))

	return disc_res_goal #.replace("not_B{0}".format(first_agent_in_tuple),"P{0}".format(first_agent_in_tuple)).replace("not_P{0}".format(first_agent_in_tuple),"B{0}_not".format(first_agent_in_tuple))

def call_classical_planner(goal):
	plan = run_planner(-1,"{0}".format(goal),"prob_template_generation.pdkbddl",[],"domain_regression_based_disc_res.pdkbddl",False)


if __name__ == '__main__':
	if len(sys.argv) < 4:
		print("\nUsage: python disc_res.py <pdkbddl problem file> <plan file> <agent tuple file>\n")
		sys.exit(1)

	agent_tuple = []
	curr_state_file = open(sys.argv[3],'r')
	raw_lines = curr_state_file.readlines()
	for line in raw_lines:
		agent_tuple.append(line.strip())

	problem = parse_pdkbddl(sys.argv[1]) # this is the CLASSENCODEMEP function in alg 1
	problem.preprocess()
	write_file('pdkb-domain.pddl', problem.domain.pddl())
	write_file('pdkb-problem.pddl', problem.pddl())
	disjuncts_of_val_formula_and_negated_val_formula = generate_validity_formula(problem,agent_tuple,sys.argv[2]) # this is the COMPUTEPLANVALIDITYFORMULA function in alg 1
	disc_res_goal = formulate_discrepancy_resolution_goal(disjuncts_of_val_formula_and_negated_val_formula,agent_tuple)
	discrepancy_resolving_plan = run_planner(disc_res_goal) # this is the CALLCLASSICALPLANNER function in alg 1
	parse_plan()
