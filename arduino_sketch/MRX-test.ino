// Файл: MRX_Universal_Indicator.ino
// Версия: 1.0
// Описание: Скетч для Arduino, который принимает текстовые команды через Serial-порт
// и выполняет соответствующие световые паттерны на светодиоде.

#define LED_PIN 8 // Пин, к которому подключен светодиод. Можете поменять, если нужно.

// --- Функции для световых паттернов ---

// Быстрое мигание (для кондиционера)
void blinkFast(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

// Паттерн "вниз" (для опускания окон)
void blinkPatternDown() {
  // 2 быстрых - пауза - 1 долгий
  digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW); delay(150);
  digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW); delay(300);
  digitalWrite(LED_PIN, HIGH); delay(500); digitalWrite(LED_PIN, LOW);
}

// Паттерн "вверх" (для поднятия окон)
void blinkPatternUp() {
  // 1 долгий - пауза - 2 быстрых
  digitalWrite(LED_PIN, HIGH); delay(500); digitalWrite(LED_PIN, LOW); delay(300);
  digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW); delay(150);
  digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW);
}

// Паттерн для диагностики (очень быстрое мерцание)
void blinkDiagnostics() {
  for (int i = 0; i < 20; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
}

// --- Основные функции Arduino ---

void setup() {
  // Запускаем Serial-порт для общения с компьютером/Raspberry Pi на скорости 9600 бод
  Serial.begin(9600);
  
  // Настраиваем пин светодиода как выход
  pinMode(LED_PIN, OUTPUT);
  
  // Отправляем в компьютер сообщение, что мы готовы к работе
  Serial.println("MRX Universal Indicator Ready.");
}

void loop() {
  // Постоянно проверяем, пришли ли данные в Serial-порт
  if (Serial.available() > 0) {
    // Читаем всю строку до символа новой строки '\n'
    String command = Serial.readStringUntil('\n');
    command.trim(); // Убираем лишние пробелы и невидимые символы

    // Выводим в монитор порта то, что мы получили (для отладки)
    Serial.print("Executing pattern for command: ");
    Serial.println(command);

    // --- Логика обработки команд ---
    
    // Фары
    if (command == "lights_on") {
      digitalWrite(LED_PIN, HIGH); // Просто включаем
    } else if (command == "lights_off") {
      digitalWrite(LED_PIN, LOW); // Просто выключаем
    }
    
    // Кондиционер
    else if (command == "ac_on") {
      blinkFast(5); // 5 быстрых вспышек
    } else if (command == "ac_off") {
      blinkFast(2); // 2 быстрых вспышки
    }
    
    // Окна (обрабатываем любую команду, содержащую "down" или "up")
    else if (command.indexOf("down") != -1) {
      blinkPatternDown();
    } else if (command.indexOf("up") != -1) {
      blinkPatternUp();
    }
    
    // Двери
    else if (command == "doors_lock") {
      // Одна короткая вспышка
      digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW);
    } else if (command == "doors_unlock") {
      // Две коротких вспышки
      digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW); delay(200);
      digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW);
    }
    
    // Диагностика
    else if (command == "run_diagnostics") {
      blinkDiagnostics();
    }
  }
}