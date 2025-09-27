# mrx_project/manage_profiles.py
from voice import speaker_id

def main():
    while True:
        print("\n--- Управление профилями водителей ---")
        print("1. Создать новый профиль")
        print("2. Выйти")
        choice = input("Выберите действие: ")

        if choice == '1':
            speaker_id.create_profile()
        elif choice == '2':
            break
        else:
            print("Неверный выбор.")

if __name__ == "__main__":
    main()