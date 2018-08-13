

##########################
### CLASS MODELCHECKER ###
##########################

# Simple model checking
class modelChecker():


    # check is a lambda method with one param: lambda data : CHECK A CONDITION
    def model_check(self,data,check,message="None"):
        try:
            assert check(data), message
            return 0 ## 0 = Success
        except AssertionError as e:
            print("[ERROR] Model Checking failed with {}".format(e))
            return 1  ## 1 = Error


