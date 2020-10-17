from src import TkinterEditor

def main():
    editor = TkinterEditor(algConfigPath="config/algo.ini")
    editor.mainloop()


if __name__ == "__main__":
    main()