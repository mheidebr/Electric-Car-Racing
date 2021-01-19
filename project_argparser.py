import argparse

#Creating the parser
parser = argparse.ArgumentParser(description="Electric car racing simulation")

#This class is meant to make it easier to enter two correct inputs and check against them
#Preferably the name you give to an object of this class would be the same (or as close to the same without conflict) as the name of the argument created within it
#...to allow for easily calling arg_check() (ex:logging_arg.arg_check(args.logging))
class SingleArg:

    def __init__(self, parser, key, lng_key, help_msg, on_msg, off_msg):
        #Adds an argument with the key (ex: -l), name (ex: --logging), and help message to be displayed when entering -h
        parser.add_argument(key, lng_key, type=str, help=help_msg)
        #This sets the strings for which input will be checked against in arg_check()
        self.on_msg = on_msg
        self.off_msg = off_msg
    
    def arg_check(self, input):
        if (input == self.on_msg):
            return True
        elif (input == self.off_msg):
            return False
        else:
            return False
            #raise argparse.ArgumentTypeError('Invalid input — use -h for more information on arguments.') 

    #My thought is — in the future more methods like arg_check() can be implemented to allow for checking on non-binary arguments such as file names, etc.

def call_args():
    #My thought is that when new arguments are needed, they can be instantiated here and each object's arg_check() method can help with correcting input   
    return parser.parse_args()

logging_arg = SingleArg(parser, '-l', '--logging', 'Turn logging on or off — enter either "on" or "off". This defaults to on with no argument.', 'on', 'off')

#Test area for args
if __name__ == "__main__":
    pass
    