import sys
import pickle

def make_plan(scenario):
    # TODO
    return False

def main(args):
    scenario = pickle.load(open('example.pkl'))

    plan = make_plan(scenario)

    print(plan)

if __name__ == '__main__':
    main(sys.argv)
