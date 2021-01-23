import argparse
import os.path

#This class is meant to make it easier to enter two correct inputs and check against them
#Preferably the name you give to an object of this class would be the same (or as close to the same without conflict) as the name of the argument created within it
#...to allow for easily calling arg_check() (ex:logging_arg.arg_check(args.logging))
class SingleArg:

    def __init__(self, parser, key, lng_key, help_msg, on_msg='on', off_msg='off'):
        #Adds an argument with the key (ex: -l), name (ex: --logging), and help message to be displayed when entering -h
        parser.add_argument(key, lng_key, type=str, default=off_msg, help=help_msg)
        #This sets the strings for which input will be checked against in arg_check()
        self.on_msg = on_msg
        self.off_msg = off_msg
    
    #for binary error checking
    def arg_check(self, input):
        if (input == self.on_msg):
            return True
        elif (input == self.off_msg):
            return False
        else:
            raise argparse.ArgumentTypeError('Invalid input — use -h for more information on arguments.') 
    
    #for checking if a file exists in the working directory
    def open_file(self, input):
        if not os.path.exists(input):
            raise argparse.ArgumentTypeError('The file %s is not in the working directory' % input)
        else:
            return open(input, 'r')

