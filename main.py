import perception.object as obj
import calibration.Calibration_App as calib
import perception.robot_move as move
import perception.shape as col
import subprocess
import sys

# calib.main()
# obj.main()
# move.main(None,'circle')
# col.main()

def run_streamlit():
    subprocess.run(["streamlit", "run", "ui/ui.py"])

def main():
    print("==================================================================================")
    print("Welcome to the Machine Vision Project!")
    print("==================================================================================")
    print("1. Run Calibration")
    print("2. Run Object Detection")
    print("3. Run Shape & Color Detection")
    print("4. Run Robot Movement")
    print("5. Run Streamlit UI")
    print("6. Exit")
    print("==================================================================================")

    choice = input("Please select an option (1-6): ")

    switch = {
        '1': calib.main,
        '2': lambda: (obj.main(), calib.Open_Image("./output/Markdown_Image.png")),
        '3': lambda: (col.main(), calib.Open_Image("./output/Color_Shape.png")),
        '4': move.main(),
        '5': run_streamlit,
        '6': lambda: sys.exit("Exiting program. Goodbye!")

    }

    func = switch.get(choice, lambda: print("Invalid option. Please select 1-6."))

    try:
        func()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.") 

if __name__ == "__main__":
    while True:
        main()
