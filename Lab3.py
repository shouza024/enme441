import random as rd

#Mastermind Game
# Sequence Generation
sequence = []
i=0
while i<=3:
    random = rd.randrange(1,7,1)
    sequence.append(random)
    i=i+1

#Inital Output
print("Guess a sequence 4 values from 1-6\n○ = one element is in the code but in the wrong place\n● = one element is in the code and in the correct place")
print()



#Taking Use Input 
condition_won =False
range_boolean =False
for n in range(12):
    while True:
        try:
            print("Guess a sequence 4 values from 1-6 ")
            input_str = input(f"Guess {n+1} of 12: ")
            guess = [int(x) for x in input_str]
        except ValueError:
            print("Not a number")
        for z in guess:
            if not (1<=z<=6):
                print(f"Number {z} must be from 1-6, try again\n")
                range_boolean =True
                break
        if range_boolean == True: continue

        if len(guess) == 4:
            break
        else:
            print()
            print("Must be 4 values,try again")

#create the str with the dots
    checker = []
    for v in range(4):
        if sequence[v] == guess[v]:
            checker.append('\u25CF')
        elif guess[v] in sequence:
            checker.append('\u25CB')
    
    for s in checker: print(s,end="")
    print("\n\n")

    #Winner message
    if sequence == guess:
        print("Correct - you win!")
        condition_won = True
        break

#Lost message
if condition_won ==0:
    print("You Lost")
    print(f"Correct Sequence: ",end="")
    for d in sequence: print(d,end='')

#Text written from local computer





