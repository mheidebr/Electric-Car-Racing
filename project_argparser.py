import argparse
import os.path
import csv
import ast

class SingleArg:

    def __init__(self, parser, key, lng_key, help_msg, on_msg, off_msg):
        #Adds an argument with the key (ex: -l), name (ex: --logging), and help message to be displayed when entering -h
        parser.add_argument(key, lng_key, type=str, help=help_msg)
        #This sets the strings for which input will be checked against in arg_check()
        self.on_msg = on_msg
        self.off_msg = off_msg
    
    #argument checking for on/off or other binary arguments
    def arg_check(self, input):
        if (input == self.on_msg):
            return True
        elif (input == self.off_msg):
            return False
        else:
            raise argparse.ArgumentTypeError('Invalid input — use -h for more information on arguments.') 
    
    #opens csv and creates dict with keys corresponding to the headers of the fastsim car csv file format
    def open_car_dict(self, input):
        if input == None:
            input = self.off_msg
        if not os.path.exists(input):
            raise argparse.ArgumentTypeError('The file %s is not in the working directory' % input)
        else:
            with open(input, newline='') as csv_file:
                csv_data = list(csv.reader(csv_file))
        car_dict = dict()
        for i in range(len(csv_data[0])):
            car_dict[csv_data[0][i]] = eval_type(csv_data[1][i]) 

        #Summing total car mass -- function borrowed from fastsim and adapted

        """Calculate total vehicle mass.  Sum up component masses if 
        positive real number is not specified for self.vehOverrideKg"""
        ess_mass_kg = 0
        mc_mass_kg = 0
        fc_mass_kg = 0
        fs_mass_kg = 0
        if (isinstance(car_dict["vehOverrideKg"], int)):
            if (not(car_dict["vehOverrideKg"] > 0)):
                if car_dict["maxEssKwh"] == 0 or car_dict["maxEssKw"] == 0:
                    ess_mass_kg = 0.0
                else:
                    ess_mass_kg = ((car_dict["maxEssKwh"] * car_dict["essKgPerKwh"]) +
                                car_dict["essBaseKg"]) * car_dict["compMassMultiplier"]
                if car_dict["maxMotorKw"] == 0:
                    mc_mass_kg = 0.0
                else:
                    mc_mass_kg = (car_dict["mcPeBaseKg"]+(car_dict["mcPeKgPerKw"]
                                                    * car_dict["maxMotorKw"])) * car_dict["compMassMultiplier"]
                if car_dict["maxFuelConvKw"] == 0:
                    fc_mass_kg = 0.0
                else:
                    fc_mass_kg = (((1 / car_dict["fuelConvKwPerKg"]) * car_dict["maxFuelConvKw"] +
                                car_dict["fuelConvBaseKg"])) * car_dict["compMassMultiplier"]
                if car_dict["maxFuelStorKw"] == 0:
                    fs_mass_kg = 0.0
                else:
                    fs_mass_kg = ((1 / car_dict["fuelStorKwhPerKg"]) *
                                car_dict["fuelStorKwh"]) * car_dict["compMassMultiplier"]
                car_dict["vehKg"] = car_dict["cargoKg"] + car_dict["gliderKg"] + car_dict["transKg"] * \
                    car_dict["compMassMultiplier"] + ess_mass_kg + \
                    mc_mass_kg + fc_mass_kg + fs_mass_kg
            #if positive real number is specified for vehOverrideKg, use that
            else:
                car_dict["vehKg"] = car_dict["vehOverrideKg"]
        else:
            if car_dict["maxEssKwh"] == 0 or car_dict["maxEssKw"] == 0:
                ess_mass_kg = 0.0
            else:
                ess_mass_kg = ((car_dict["maxEssKwh"] * car_dict["essKgPerKwh"]) +
                            car_dict["essBaseKg"]) * car_dict["compMassMultiplier"]
            if car_dict["maxMotorKw"] == 0:
                mc_mass_kg = 0.0
            else:
                mc_mass_kg = (car_dict["mcPeBaseKg"]+(car_dict["mcPeKgPerKw"]
                                                * car_dict["maxMotorKw"])) * car_dict["compMassMultiplier"]
            if car_dict["maxFuelConvKw"] == 0:
                fc_mass_kg = 0.0
            else:
                fc_mass_kg = (((1 / car_dict["fuelConvKwPerKg"]) * car_dict["maxFuelConvKw"] +
                            car_dict["fuelConvBaseKg"])) * car_dict["compMassMultiplier"]
            if car_dict["maxFuelStorKw"] == 0:
                fs_mass_kg = 0.0
            else:
                fs_mass_kg = ((1 / car_dict["fuelStorKwhPerKg"]) *
                            car_dict["fuelStorKwh"]) * car_dict["compMassMultiplier"]
            car_dict["vehKg"] = car_dict["cargoKg"] + car_dict["gliderKg"] + car_dict["transKg"] * \
                car_dict["compMassMultiplier"] + ess_mass_kg + \
                mc_mass_kg + fc_mass_kg + fs_mass_kg
        
        #End of fastsim code
        
        return car_dict
    
    #opens csv file and returns a dict with keys "air_density" and integers representing breakpoints
    def open_track_dict(self, input):
        if input == None:
            input = self.off_msg
        if not os.path.exists(input):
            raise argparse.ArgumentTypeError('The file %s is not in the working directory' % input)
        else:
            with open(input, newline='') as csv_file:
                csv_data = list(csv.reader(csv_file))[1]
        track_dict = dict()
        track_dict["air_density"] = eval_type(csv_data[0])
        csv_data.pop(0)
        for i in range(int(len(csv_data)/2)):
            track_dict[eval_type(csv_data[2*i])] = eval_type(csv_data[(2*i)+1])
        return track_dict


#call_args() now instantiates each SingleArg object and adds them to a dictionary, as well as the data structure filled with parsed args
def call_args():
    parser = argparse.ArgumentParser(description="Electric car racing simulation")

    arg_dict = dict()
    arg_dict["logging_arg"] = SingleArg(parser, '-l', '--logging', 'Turn logging on or off — enter either "on" or "off". This defaults to off with no argument.', 'on', 'off')
    arg_dict["car_arg"] = SingleArg(parser, '-c', '--car', 'Load a custom car configuration — defaults to included file default_car.csv.', 'void', 'fastsim_car_test.csv')
    arg_dict["track_arg"] = SingleArg(parser, '-t', '--track', 'Load a custom track configuration — defaults to included file track.csv.', 'void', 'high_plains_track.csv')
    arg_dict["output_arg"] = SingleArg(parser, '-o', '--output', 'Specify a name for an output file — defaults to "output.csv" by default.', 'void', 'output.csv')
    arg_dict["parsed_args"] = parser.parse_args()

    return arg_dict

#for flexible type conversion -- may not be a permanent solution
def eval_type(input):
    try:
        input = ast.literal_eval(input)
    except:
        pass
    return input

if __name__ == "__main__":
    args = call_args()
    car_data = args["car_arg"].open_car_dict(args["parsed_args"].car)

    print(car_data)

    