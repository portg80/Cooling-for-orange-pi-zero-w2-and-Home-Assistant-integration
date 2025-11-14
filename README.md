# Охлаждение для orange pi zero w2 | Home Assistant интеграция | Node-Red оповещения о неисправности охлаждения

!!!В ПРОЦЕССЕ НАПИСАНИЯ!!!

Это проект включает в себя инструкцию как самому **сделать для orange pi zero w2 активное охлаждение кулером** (вентилятором) **с управлением скоростью вращения**. 

Также через MQTT мы будем отображать показатели системы охлаждения прямо в Home Assistant (далее иногда буду называть его "HA") и из него же сможем менять ее настройки.

Сделаем на **Node-Red систему оповещения о критических ситуациях** (если вентилятор помрет и перестанет крутится мы сразу об этом узнаем) уведомлением на телефон, и даже **озвучим экстренное сообщение через Яндекс Алису**!

Написано так, чтобы даже новичок разобрался. 

Я буду иногда расшифровывать сокращения по типу "ШИМ" вот так в скобках: "ШИМ (PWM) («мощности»)" для большей ясности.

## Вот что мы получим в конце:

<img width="2560" height="1280" alt="image" src="https://github.com/user-attachments/assets/8251fcb3-5214-4ed4-8772-b2786988df85" />

Это сама панель управления внутри Home Assistant (HA). 


На графиках отображаются:
- **Температура процессора** (CPU) (получаем через MQTT)
- **Частота ШИМ** (значение от 0 до 1024, чем больше - тем быстрее крутится вентилятор, другими словами "мощность") (получаем через MQTT)
- **Скорость вращения вентилятора** RPS (обороты кулера в секунду) (получаем через MQTT)
- **CPU использование**, нагрузка на процессор в процентах (стандартный датчик HA)

Слайдеры меняют настройки работы системы:
- **Пороги температур:** 

    **Первый слайдер «Temp для 100% вращения»** устанавливает значение температуры процессора, при котором PWM (ШИМ), то есть «мощность» вентилятора, будет максимальной.    
    
    **Второй слайдер "Temp для 0% вращения"** устанавливает ту температуру, при которой вентилятор будет работать на минимальной «мощности», а когда температура опустится ниже, то вовсе отключится

- **Пороги ШИМ** (PWM) («мощности») как раз таки устанавливают минимальный и максимальный порог мощности работы вентилятора. Почему минимальный у меня = 950 PWM? Подобрал это опытным путем, ибо при меньших значениях МОЙ вентилятор за 60р просто не может стартануть.

<img width="1028" height="658" alt="image" src="https://github.com/user-attachments/assets/15444a29-e657-4fb1-9ddc-198bd7b1ef5d"/>

**Система предупреждения о неисправности:**

<img width="1033" height="703" alt="image" src="https://github.com/user-attachments/assets/bc363b2d-34fd-4cf5-814c-c79f25228ce0"/>

Видео-демонстрация сигнализации с оповещением через алису:

https://github.com/user-attachments/assets/526eb54d-f185-41ab-abf6-150ad8f4b349

<img width="585" height="771" alt="image" src="https://github.com/user-attachments/assets/ee9e26f1-fbef-49ca-aa60-f29ca2713a66" />


https://github.com/user-attachments/assets/947b8b01-0ef1-4230-bbaa-66d4df62416a

# Как это выглядит в жизни

<img width="2131" height="787" alt="image" src="https://github.com/user-attachments/assets/45c71ee4-ca26-4b38-b247-b20534737212"/>
<img width="1414" height="766" alt="image" src="https://github.com/user-attachments/assets/939fc397-2d03-4cc7-bb22-bd8d59c58f3f"/>
<img width="957" height="1602" alt="image" src="https://github.com/user-attachments/assets/1341169d-4998-46e3-b951-b53c131e9d5a"/>
Плата:
<img width="1042" height="786" alt="image" src="https://github.com/user-attachments/assets/fc202f43-46d7-44d2-b2c8-30a20651d062"/>

Считаю что моя _идеальная_ пайка заслуживает того чтобы вы **поставили звезду этому репозиторию OwO.** (я просто перепаивал по 10 раз, поэтому так страшно, но работает безотказно)

# Принцип работы
Сразу скажу, на картинке 3 orange pi, но по факту ЭТО ОДИН И ТОТ ЖЕ модуль, просто я разбил на компоненты для наглядности.

Мой Python скрипт посылает данные в плагин MQTT, а из плагина MQTT они становятся объектами(устройствами). HA откуда их читает для графиков в панели. Так же их отслеживает моя автоматизация в плагине Node-Red, для уведомлений о поломке вентилятора.

Изменение настроек работает примерно по такому же принципу, но в обратную сторону.

<img width="1018" height="764" alt="image" src="https://github.com/user-attachments/assets/bfaffe23-870e-411a-96d9-f422e8b1e9d8" />


# Что купить?
**Цены в российских рублях, актуальные на 14.11.2025**

1 шт. - [MF-25 (С2-23) 0.25Вт, 10 кОм, 1%, Резистор металлопленочный
](https://www.chipdip.ru/product/mf-25-s2-23-0.25vt-10-kom-1-rezistor-metalloplenochnyy-41486) (5 руб)

1 шт. - [CF-25 (С1-4) 0.25Вт, 1 кОм, 5%, Резистор углеродистый](https://www.chipdip.ru/product/cf-25-s1-4-0.25vt-1-kom-5-rezistor-uglerodistyy-44435) (3.80 руб)

1 шт. - [MO-50 (С2-23) 0.5Вт, 470 Ом, 5%, Резистор металлооксидный](https://www.chipdip.ru/product/mo-50-s2-23-0.5vt-470-om-5-rezistor-metallooksidnyy-9000040045) (3.80 руб)

1 шт. - [1N4001, Диод выпрямительный 1А 50В [DO-41 / DO-204AC.]](https://www.chipdip.ru/product/1n4001-diod-vypryamitelnyy-1a-50v-do-41-do-204ac-diotec-9000461658) (5.70 руб)

1 шт. - [IRLZ44NPBF, Транзистор, N-канал 55В 47А logic [TO-220AB]](https://www.chipdip.ru/product/irlz44npbf-tranzistor-n-kanal-55v-47a-logic-to-220ab-infineon-38440) (84.50 руб)

1 шт. - [Макетная плата 4х6 см](https://www.chipdip.ru/product/maketnaya-plata-4x6-sm-8044995884) (32.50 руб)

1 шт. - [Флюс для пайки, паста паяльная канифольно-вазелиновая, 20 г, банка, инд. упаковка, серия "Алмаз" TDM](https://www.chipdip.ru/product/sq1025-1511-flyus-dlya-payki-pasta-payalnaya-tdm-electric-8028919866) (58.50 руб)

1 шт. - [Припой трубка с канифолью, 10 г, 0,8 мм, ПОС-61, колба](https://www.chipdip.ru/product/pripoy-trubka-s-kanifolyu-10-g-0-8-mm-pos-61-kolba-9001150465) (100 руб)

1 шт. - [EX295193RUS, Вентилятор 5В DC ExeGate EX04010S3P-5 (40x40x10 мм, Sleeve bearing (подшипник скольжения), 3pin, 5000RPM, 24dBA)](https://www.chipdip.ru/product/ex295193rus-ventilyator-5v-dc-exegate-ex04010s3p-5-8038575118) (62 руб)

4 шт. используется в проекте, но брал набор из 40 - [Соединительные провода «папа-мама» (40 шт. / 20 см), Шлейф из 40 проводов для прототипирования электронных устройств
](https://www.chipdip.ru/product/soedinitelnye-provoda-papa-mama-40-sht-20-sm-shleyf-iz-9001322248) (200 руб)

2 шт. используется в проекте, но брал набор из 5 - [JST PH 2.0мм 4pin кабель с разъемом](https://www.ozon.ru/product/kabel-dlya-podklyucheniya-periferiynyh-ustroystv-0-15-m-krasnyy-chernyy-2368560758/?at=Brtz2BAv9IApANKMigDmRj6uvKN3zQF0JA1j2ur9noMW) (~150р)

**ИТОГО: ~705 рублей** с набором проводов и коннекторами, без них цена ~350 руб, можно сэкономить на наборах поменьше или найти поштучно.

# Схема пайки и подключения
**Страшная принципиальная:**

<img width="1315" height="799" alt="image" src="https://github.com/user-attachments/assets/dbce08c2-b91f-4f59-b46a-b8aab996bda9" />

**Вот схема подключения с подписями каждого пина (контакта):**

<img width="1317" height="602" alt="image" src="https://github.com/user-attachments/assets/9a6d0b24-5847-4819-ad20-98152d53234a" />

GND можно воткнуть в любой свободный, а PWM read и PWM control переназначить в моем скрипте (PWM control только на пин с поддержкой ШИМ, по типу PWM1 PWM2 на картинке).


# Устанавливаем и настраиваем Python скрипт 
Скрипт находится в файле **pwm_fan_daemon.py**, можете открыть его где вам удобно в текстовом редакторе и поменять нужные настройки. 

## настроим MQTT на Home Assistant
**Создадим отдельного пользователя именно для mqtt.**
**В Home Assistant:**
 
**Настройки -> Люди -> Пользователи -> Добавить пользователя (галочка администратора НЕ нужна) -> задаем имя и пароль и нажимаем добавить**

<img width="1920" height="952" alt="image" src="https://github.com/user-attachments/assets/fca8054c-92bd-4f43-b4fc-54a0b0261af3" />

**В Home Assistant:**
**Настройки -> Дополнения -> Магазин дополнений -> в поиске ищем "Mosquitto broker" и устанавливаем -> открываем его и вверху вкладка конфигурация есть, переходим на нее -> в категории Logins нажимаем кнопку "Добавить" -> вписываем логин и пароль пользователя созданного на предыдущем шаге**

Выглядеть все должно примерно так:

<img width="1321" height="907" alt="image" src="https://github.com/user-attachments/assets/0f0b605a-728f-4270-959b-f79bcffbc58d" />
<img width="1314" height="279" alt="image" src="https://github.com/user-attachments/assets/8dd52c81-65ca-4d23-8612-4aab6ca93e5e" />


## какие настройки нужно изменить:

Имя скрипта **pwm_fan_daemon.py**, в нем находится код в виде обычного текста. Открыть можно в любом текстовом редакторе

Менять нужно эти настройки (ищите через поиск по файлу названия переменных по типу MQTT_USER, TEMP_CHECK_INTERVAL и остальные, и меняем значения после равно):

```bash
...
TEMP_CHECK_INTERVAL = 8 # Время интервала сканирования температуры в секундах и отправки данных на сервер MQTT в секундах. Например тут через каждые 8 секунд.
...
# MQTT-настройки
MQTT_BROKER = "ВАШ_АДРЕС_HOME_ASSISTANT"  # тут ваш адрес Home Assistant, без порта! Например: MQTT_BROKER = "192.168.1.21"
MQTT_PORT = 1883   # это стандартный прорт MQTT. Можно поменять в настройках плагина MQTT если хотите а потом и тут, я не менял.
MQTT_USER = "ВАШ_USER_NAME_СОЗДАННОГО_ПОЛЬЗОВАТЕЛЯ" # имя пользователя для входа. Например: MQTT_USER = "mqtt-user"
MQTT_PASSWORD = "ВАШ_ПАРОЛЬ_СОЗДАННОГО_ПОЛЬЗОВАТЕЛЯ" # ваш пароль для входа в созданного пользователя. Например: MQTT_PASSWORD = "hhe7f2@HD$@#5D!fe2"
...
```

Читайте текст после символа решетки (#), там описано что за что отвечает. Обратите внимание, что значения в итоге **должны быть в кавычках!** 
 
**Например это:**

```bash
 MQTT_BROKER = "ВАШ_АДРЕС_HOME_ASSISTANT"
```
 вы измените на ваш адрес Home Assistant, у меня например это **192.168.1.33**:
```bash
 MQTT_BROKER = "192.168.1.33"
```

Пример как искать нужные параметры в блокноте:
Чтобы открыть поиск нажимаем "ctrl+F" вводим имя настройки и переключаемся стрелочками.

<img width="1519" height="1015" alt="image" src="https://github.com/user-attachments/assets/87351e28-220b-4258-95ef-ab2688f7f347" />

После изменения сохраняем файл pwm_fan_daemon.py. 

## скидываем скрипт pwm_fan_daemon.py на сервер и делаем исполняемым

Дальше его нужно поместить в папку на самом сервере. Я использую для этого SSH подключение через клиент для Windows [MobaExtern](https://mobaxterm.mobatek.net/) (очень его советую).

_PS вставлять команды можно щелкнув Правой кнопкой мыши (ПКМ) и выбрав в меню пункт_ **Paste** 

<img width="1436" height="789" alt="image" src="https://github.com/user-attachments/assets/6ecf8117-29bb-49bf-bcf9-6055d04d3e86" />


Как создать подключение SSH смотри в видео:

https://github.com/user-attachments/assets/28122663-20dd-4611-845b-ef6d103ae84d

Дальше создадим в папке **/opt** папку **PWM_FAN** и в нее перетащим наш скрипт.

Должно получится так: **/opt/PWM_FAN/pwm_fan_daemon.py**

**В видео показываю как это сделать:**

https://github.com/user-attachments/assets/3268b96f-954e-430a-b30e-782044d7fafe

Далее в консоли переходим в эту папку и делаем файл исполняемым с помощью команд:

```bash
cd /opt/PWM_FAN/
sudo chmod +x pwm_fan_daemon.py
```


## Устанавливаем зависимости для работы скрипта

Обновим системные пакеты и установим зависимости:

```bash
cd /root/
sudo apt update && sudo apt upgrade -y
sudo apt install -y git
sudo apt install python3-pip
```

Установим python библиотеку paho-mqtt для MQTT соединений:

```bash
cd /root/
sudo pip3 install --break-system-packages paho-mqtt
```

Теперь установим python библиотеку wiringOP (wiringPi) для поддержки управления пинами. Без нее ничего не будет работать:

```bash
cd /root/
apt-get update
apt-get install -y git
git clone https://github.com/orangepi-xunlong/wiringOP.git
cd wiringOP
sudo ./build clean
sudo ./build
```

После установки проверьте все ли установилось и работает этой командой:

```bash
gpio readall
```

Вывод должен быть примерно такой:

 <img width="1001" height="789" alt="image" src="https://github.com/user-attachments/assets/f2914797-0754-45ab-a5b0-4a3ea60d10f2"/>

 

## Теперь добавим наш скрипт в автозагрузку, чтобы при запуске сервера он автоматически включался и начинал работу

Создадим файл с помощью текстового редактора nano, для этого пишем в консоль:

```bash
sudo nano /etc/systemd/system/pwmfan.service
```

После команды файл сразу откроется в редакторе, вставляем туда этот код (ПКМ -> Paste):
```bash
[Unit]
Description=PWM Fan Control Service
After=multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/PWM_FAN
ExecStart=/usr/bin/python3 -u /opt/PWM_FAN/pwm_fan_daemon.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

Выглядеть должно так:

<img width="1032" height="519" alt="image" src="https://github.com/user-attachments/assets/d86b316e-cf21-4165-b25c-fd3158606493" />

Чтобы сохранить и выйти тут нужно нажать ctrl+X

Появится окно с подтверждением, нажимаем Y:

<img width="745" height="336" alt="image" src="https://github.com/user-attachments/assets/e2e891b9-4497-427e-a4a5-c7e7d72838b3" />

И появится еще одно окно с подтверждением о пути и имени файла, нажимаем Enter:

<img width="745" height="344" alt="image" src="https://github.com/user-attachments/assets/89f6f70f-1be9-4e16-9c71-8bb8fd7e376d" />

Если все норм, редактор закроется и вернет вас в терминал:

<img width="745" height="40" alt="image" src="https://github.com/user-attachments/assets/0045d7b5-5a5c-47d6-9c22-16f05822a4a0" />


Чтобы убедится что вы сделали все правильно можете опять открыть этот файл и посмотреть сохранилось ли все в нем, и не пустой ли он:
```bash
sudo nano /etc/systemd/system/pwmfan.service
```


Теперь нам нужно активировать этот сервис, в консоли вводим поочередно следующие команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pwmfan.service
sudo systemctl start pwmfan.service
```

ГОТОВО - СЕРВИС ЗАПУЩЕН!

**Проверка статуса:**

```bash
sudo systemctl status pwmfan.service
```

<img width="836" height="322" alt="image" src="https://github.com/user-attachments/assets/fbdcf877-df24-48ce-afff-0e9a8b8294ba" />

### КОМАНДЫ ОБСЛУЖИВАНИЯ СЕРВИСА АВТОЗАГРУЗКИ:

**Просмотр логов:** 
```bash
journalctl -u pwmfan.service -f
```

**Перезапуск сервиса:** 
```bash
sudo systemctl restart pwmfan.service
```

**Остановить сервис:**
```bash
sudo systemctl stop pwmfan.service
```

**Если нужно выключить автозапуск при загрузке:**
```bash
sudo systemctl disable pwmfan.service
```

**Включить автозапуск обратно:**
```bash
sudo systemctl enable pwmfan.service
```

**Удалить автозагрузку полностью (сам скрипт останется на диске):**
```bash
sudo rm /etc/systemd/system/pwmfan.service
sudo systemctl daemon-reload
```
