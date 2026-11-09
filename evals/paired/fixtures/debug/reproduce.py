from admitter import Admitter

admitter = Admitter()
print("first:", admitter.admit("first", 0))
print("second:", admitter.admit("second", 1))
print("drain:", admitter.drain())
print("retry:", admitter.admit("second", 2))
