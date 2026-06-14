Ориг гайд: [Installing HAOS with Armbian Bookworm 12 - Haade.fr](https://haade.fr/en/blog/easy-installation-home-assistant-os-armbian-cubietruck-2024#prerequisites)

Armbian - это дебиан 12 версии пересобранный командой разрабов под различные одноплатники и конфигурации. 
По сути Linux для плат разработки ARM. 
А Orange PI zero 2w то <span style='color:var(--mk-color-red)'>ARM 64 (armv8)</span> или точнее <span style='color:var(--mk-color-red)'>aarch64</span>. И та и та пометка подходит, но если есть вторая то выбираем ее, она более "подогнана/конкретна".
[^1]
# Запись образа системы на флешку и запуск
1. **Скачиваем нужный образ с офф сайта:**
[ОФИЦИАЛЬНЫЙ САЙТ ARMBIAN orange pi zero 2w](https://www.armbian.com/orange-pi-zero-2w/)
> *Там есть 2 версии минимальная (~200МБ), содержит минимум предустановленных библиотек и пакетов и XFCE  (~1.5Гб)  - с графическим интерфейсом. Изначально выбрал с граф. Все дальнейшие команды были выполнены на ней, в минимальной версии мб потребуется что то доустанавливать.*

<mark style='background:var(--mk-color-yellow)'>Загрузка образа Armbian</mark>
[2025-08-12 19-26-11.mkv](2025-08-12%2019-26-11.mkv)
2. Качаем [balenaEtcher - Flash OS images to SD cards & USB drives](https://etcher.balena.io/)
   выбираем образ, флешку и нажимаем flash. (Он сначала шьет потом проверяет, поверка скипается)
   ![[Pasted image 20250701224655.png]]
<mark style='background:var(--mk-color-yellow)'>   Загрузка balenaEtcher</mark>
   [2025-08-12_20-06-04.mkv](2025-08-12_20-06-04.mkv)
<mark style='background:var(--mk-color-yellow)'>   Форматир и прошивка</mark>
   [2025-08-12_20-16-35.mkv](2025-08-12_20-16-35.mkv)
3. Вставляем флешку, первый запуск может занять около 10 минут, прежде чем можно будет подключится к пк через SSH или граф интерфейс. К сети подрубаем Ethernet. У меня вайфай на нем нестабилен.
   
4. Узнать ip машины можно через админку роутера 192.168.0.1 или 192.168.1.1
  <mark style='background:var(--mk-color-red)'> В ней же нам нужно сделать статичным ip адрес Orange pi</mark> 
  
  [2025-08-20_21-47-04.mkv делаем статичный ip](2025-08-20_21-47-04.mkv)
   ~~Вот есть из линукса команда для подключения по SSH~~ `ssh -p 22 ton-ip -l root` . 
   Основа у меня винда, поэтому для SSH использую удобный [MobaXterm](https://mobaxterm.mobatek.net/download.html)
![[Pasted image 20250701225723.png]]
<span style='color:var(--mk-color-yellow)'>Пароль по умолчанию для пользователя root будет **1234**</span>
Загрузка и установка mobaExtern 
[2025-08-12_20-33-09.mkv](2025-08-12_20-33-09.mkv)
Подключаемся по ssh через нее:
[2025-08-20_23-11-38.mkv](2025-08-20_23-11-38.mkv)
## **Ошибка запуска службы ssh и ее решение:**
[Ответ](https://askubuntu.com/questions/603493/apt-get-dependency-issue-open-ssh-client?_gl=1*uevuei*_ga*MTk2MjcyMTU1Ny4xNzU1NzE3ODUx*_ga_S812YQPLT2*czE3NTU3MTc4NTAkbzEkZzAkdDE3NTU3MTc4NTIkajYwJGwwJGgw)

Если не запускается ssh и при проверке статуса командой:
```
sudo service ssh status
```
вылетает что не активен(видосы и фотки с телефона) и красный коричневый текст тогда вам сюда.
Должно быть вот так:
![[Pasted image 20250820230415.png]]

Просто удалите эти пакеты, чтобы можно было использовать apt для других пакетов. Выполните эти команды в терминале.
```
sudo apt-get remove openssh-server openssh-client --purge && sudo apt-get autoremove && sudo apt-get autoclean && sudo apt-get update
```
Затем переустановите сервер и клиент OpenSSH.
```
sudo apt-get install openssh-server openssh-client
```

Ошибка входа в рут по ssh:
при подключении ввода логина root и пароля от него запрещает доступ:
```
login as: root
▒root@192.168.1.33's password:
Access denied
```

Отредактируйте конфигурационный файл:
```
sudo nano /etc/ssh/sshd_config
```
Найдите строки и измените ее:
```shell
# Было:
# PermitRootLogin no
...
#PasswordAuthentication no

# Стало:
PermitRootLogin yes
...
PasswordAuthentication yes
```



тут дальше видео с телефона
# Настройка Armbian
**При первом запуске Armbian попросит вас:**
- установите новый пароль для root
- выберите для установки командную оболочку zsh или **bash**. (иногда не просит хз)
  Я ВЫБРАЛ BASH тк это самый стандартный выбор
- создайте пользователя без рута (необязательно)
- создайте пароль для этого пользователя
- настройка языковой системы пользователя.

Обновим систему и все пакеты:
```Shell
sudo apt update
sudo apt upgrade -y
```
Опционально очистка ненужных пакетов
```Shell

sudo apt autoremove -y
sudo apt clean

```
Перезагружаемся!!!:
```Shell
sudo reboot
```


  ## Конфиг armbian
 ** После перезагрузки подключитесь через ssh и перейдите в [конфигурацию Armbian](https://docs.armbian.com/User-Guide_Armbian-Config/)**
 
 [Armbian for beginners / armbian-config - YouTube](https://youtu.be/i9KyATAmfwQ)
```Shell
armbian-config
```
Можем настроить сети, вайфай, блютуз, обновы и тд..

## Подготовка к HAos. 
### 1 — cgroupv1
Выйдите из Armbian (как понимаю из пользователя), чтобы иметь возможность настроить cgroupv1. 
По умолчанию Armbian работает в cgrouv2, но, оказывается, операционная система Home Assistant работает в cgroupv1.

**Перейдите к файлу armbianEnv.txt**
```Shell
nano /boot/armbianEnv.txt
```
**и вставьте этот код в конец скрипта, не забудьте сохранить Ctrl+X,  потом Y, потом Enter**
```Shell
extraargs=systemd.unified_cgroup_hierarchy=0
```

У меня конфиг получился такой:
```Shell
verbosity=1
bootlogo=true
console=both
disp_mode=1920x1080p60
overlay_prefix=sun50i-h616
rootdev=UUID=e358e491-1270-4f20-883f-27ffac9985dd
rootfstype=ext4
extraargs=systemd.unified_cgroup_hierarchy=0
usbstoragequirks=0x2537:0x1066:u,0x2537:0x1068:u
```
Редактируем группу:
[2025-08-20_23-21-37.mkv](2025-08-20_23-21-37.mkv)
### Маскируем Armbian под Debian 12 чтобы Home Assistant не ругался
**Измените название дистрибутива, чтобы оно было распознано HAOS**
```Shell
nano /etc/os-release
```
**Изменить** `PRETTY_NAME=”Armbian 23.02.2 Jammy"` **на** `PRETTY_NAME=”Debian GNU/Linux 12 (bookworm)”`
	(не забудьте сохранить Ctrl+X,  потом Y, потом Enter)
<span style='color:var(--mk-color-red)'>КАВЫЧКИ Е**НЫЕ ДОЛЖНЫ БЫТЬ РОВНЫМИ, А ТУТ ОНИ ПОЧЕМУ ТО СДЕЛАЛИСЬ С НАКЛОНОМ ИЗ ЗА ЭТОГО ВЫДАВАЛО ОШИБКУ</span>
” <span style='color:var(--mk-color-yellow)'>!=</span> "
Мой конфиг выглядит теперь так:
```Shell
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.armbian.com"
SUPPORT_URL="https://forum.armbian.com"
BUG_REPORT_URL="https://www.armbian.com/bugs"
ARMBIAN_PRETTY_NAME="Armbian 23.11.1 bookworm"
```
Маскируем:
[2025-08-20_23-24-19.mkv](2025-08-20_23-24-19.mkv)
# Установка операционной системы Home Assistant
1. **установите зависимости**
```Shell
apt install \
apparmor \
cifs-utils \
curl \
dbus \
jq \
libglib2.0-bin \
lsb-release \
network-manager \
nfs-common \
systemd-journal-remote \
systemd-resolved \
udisks2 \
wget -y
```

2. **Перезагрузка системы**
```Shell
reboot
```

3. **Установите Docker**
```Shell
curl -fsSL get.docker.com | sh
```
> *Вы получите сообщение о том, что используете Docker как пользователь без прав суперпользователя, что приведёт к появлению сообщения об ошибке в Home Assistant при первом запуске. 
> Но не волнуйтесь, вам просто нужно перезапустить Home Assistant, и он автоматически исправит ситуацию.*
```Shell
Что то типо этого будет:
To run Docker as a non-privileged user, consider setting up the
Docker daemon in rootless mode for your user:
...
WARNING: Access to the remote API on a privileged Docker daemon is equivalent
         to root access on the host. Refer to the 'Docker daemon attack surface'
         documentation for details: https://docs.docker.com/go/attack-surface/
```

Проверим что докер норм работает:
```Shell
docker run hello-world
```

Установка зависимостей и докера:
[2025-08-20_23-27-17.mkv](2025-08-20_23-27-17.mkv)
4. **Установка OS-Agent**
подготовка временного файла для загрузки:
<mark style='background:var(--mk-color-brown)'>здесь чет какой то временный пользователь _apt но у меня ошибку выдавало, я поэтому root:root писал, дипсик там что то подсказывал, или вообще не писал, нужно уточнить!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Уточнил, 2 и 3я команды можно не писать</mark>
```Shell
mkdir /tmp/download/
chown -Rv _apt:root /tmp/download/
chmod -Rv 700 /tmp/download/
cd /tmp/download/
```

Загрузите последнюю версию:
<span style='color:var(--mk-color-red)'>Версию актуальную брать отсюда:</span>
[Release · home-assistant/os-agent · GitHub](https://github.com/home-assistant/os-agent/releases/latest)
<span style='color:var(--mk-color-red)'>МЕНЯЕМ НОМЕР ВЕРСИИ И АРХИТЕКТУРУ ПРОЦЕССОРА во всех командах</span>
![[Pasted image 20250702140936.png|1300]]
wget https://github.com/home-assistant/os-agent/releases/download/1.7.2/os-agent_1.7.2_linux_aarch64.deb

dpkg -i os-agent_1.7.2_linux_aarch64.deb

```Shell
wget https://github.com/home-assistant/os-agent/releases/download/1.7.2/os-agent_1.7.2_linux_aarch64.deb

dpkg -i os-agent_1.7.2_linux_aarch64.deb
```

Проверяем установку:
```Shell
gdbus introspect --system --dest io.hass.os --object-path /io/hass/os

или как гпт сказал (на данном этапе не будет работать):

systemctl status os-agent
```

Вы должны увидеть несколько строк, как показано ниже:
```Shell
node /io/hass/os {
  interface org.freedesktop.DBus.Introspectable {
    methods:
      Introspect(out s out);
    signals:
...
    signals:
    properties:
      @org.freedesktop.DBus.Property.EmitsChangedSignal("invalidates")
      readonly s Version = '1.6.0';
      @org.freedesktop.DBus.Property.EmitsChangedSignal("true")
      readwrite b Diagnostics = false;
  };
};
```

5. **Установите управляемый установщик**
   На последнем этапе установки скрипт supervised-installer установит все контейнеры, необходимые для корректной работы Home Assistant
```Shell
wget -O homeassistant-supervised.deb https://github.com/home-assistant/supervised-installer/releases/latest/download/homeassistant-supervised.deb

apt install ./homeassistant-supervised.deb
```
Когда скрипт попросит вас, выберите архитектуру, соответствующую вашим потребностям, в моём случае <span style='color:var(--mk-color-red)'>qemuarm-64</span>

Успешный успех:
```
[info] Install supervisor startup scripts
[info] Install AppArmor scripts
[info] Start Home Assistant Supervised
[info] Installing the 'ha' cli
[warn] Could not find /etc/default/grub or /boot/firmware/cmdline.txt failed to 
switch to cgroup v1
[info] Within a few minutes you will be able to reach Home Assistant at:
[info] http://homeassistant.local:8123 or using the IP address of your
[info] machine: http://ton-ip:8123
```

# Наконец - то терпение
В зависимости от мощности вашей карты Home Assistant установка может занять больше или меньше времени, так что наберитесь терпения. В моём случае установка заняла около 20 минут. Вы можете следить за процессом, перейдя по адресу, указанному в конце скрипта супервайзера.
В моем случае http://192.168.0.33:8123 - локальный адрес нашей машины и порт 8123
[2025-08-20_23-48-09.mkv](2025-08-20_23-48-09.mkv)
## чтобы не забыть
После настройки Home Assistant не забудьте проверить наличие обновлений. Как указано выше, у вас может возникнуть ошибка Docker non-root user, но не паникуйте, просто перезапустите Home Assistant. Лично я перезапустил всю систему.
![[Pasted image 20250702024116.png]]
ошибка непривилегированного пользователя Docker

Перезагружает всю систему с помощью Home Assistant:
```
учетная запись пользователя > активировать расширенный режим
настройка> система> перезапустить home assistant > дополнительные параметры > перезапустить систему
```

# BACKUP - google drive настройка и востановление
[Резервное копирование Home Assistant по расписанию на google диск - У Павла!](https://psenyukov.ru/%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D0%BD%D0%BE%D0%B5-%D0%BA%D0%BE%D0%BF%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-home-assistant-%D0%BF%D0%BE-%D1%80%D0%B0%D1%81%D0%BF%D0%B8%D1%81%D0%B0%D0%BD/)

Чтоб установить аддон, нам нужно добавить сторонний репозиторий. Для этого зайдем в Supervisor->Add-Ons-> правый верхний угол -> Repositories и туда добавить следующий репозиторий: https://github.com/sabeechen/hassio-google-drive-backup . После этого нажимаем save и у нас <span style='color:var(--mk-color-red)'>ПОСЛЕ ПЕРЕЗАГРУЗКИ HA</span> появится новый аддон под названием Home assistant google drive backup.

Вводим буквы с аддона в гитхабе получаем код, удаляем лишние пробелы если есть и код вставляем в аддон.

Восстановить резервную копию можно из стандартного меню настроек, там на три точки справа вверху жмем и загружаем на сервер наш бэкап.
Находим его в меню вручную созданных бекапов, нажимаем на него. Там можно выбрать что именно восстанавливать галочками. И нажимаем восстановить. <span style='color:var(--mk-color-red)'>ВСЕ ВЫБРАННЫЕ ДАННЫЕ ПЕРЕЗАПИШУТСЯ</span>
![[Pasted image 20250820235328.png]]

## Ошибка 'BackupManager.do_restore_partial' blocked from execution, no host internet connection
Писал что нет интернета при попытке восстановить резервную копию, у докер контейнера не было интернета
[[ОШИБКА Нет интернета при Восстановлении из резерв копии. Попытки и отладка привели к успеху]]
# Добавляем HACS в Home Assistant
[Получаем доступ по ssh к серверу Home Assistant на HassOS - У Павла!](https://psenyukov.ru/%d0%bf%d0%be%d0%bb%d1%83%d1%87%d0%b0%d0%b5%d0%bc-%d0%b4%d0%be%d1%81%d1%82%d1%83%d0%bf-%d0%bf%d0%be-ssh-%d0%ba-%d1%81%d0%b5%d1%80%d0%b2%d0%b5%d1%80%d1%83-home-assistant-%d0%bd%d0%b0-hassos/)

[Добавляем HACS в Home Assistant - IO Home](https://io-home.ru/home-assistant/integrations/dobavljaem-hacs-v-home-assistant/)

ВНИМАНИЕ, КОМАНДА ВВОДИТЬСЯ НЕ В ТЕРИМНАЛ СИСТЕМЫ ARMBIAN, В КОТОРУЮ УСТАНОВЛЕН HomeAss, А ВВОДИМ ЕЕ В ТЕРМИНАЛ САМОГО HOME ASSISTANT!!! ЧЕРЕЗ АДДОН ЭТО ДЕЛАЕТСЯ!


Включаем расширенный режим (нажимаем на значок профиля)

Генерируем ключи RSA для SSH:
В мобаЕкстерн:
Tools -> MobaKeyGen (SSH key generator)

В окошке будет публичный ключ:
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCSPH0v/sZhlXGnkHP9ezA/0xRp60JFHWv9onc9kbmUXhkcN9KwwfexXecDndZkH/xTubfoZUpqXKMHRVeg2fnjytkCNF/xYMrmLuus/ob7YKLE5dA7I4WNpw/0RsSlJz8fvDbv/OHme9PPpX0lpEAMxAQ1kjYN92R2gJAQHX0T9bvHGEO4UKCxl4xDIdHUW9H6vplOiRUjwuLurxuqYx5LLdRpAS9sAM6+8Em5a7sWNIQ2lcJ/5z4BDpU0JOrBfCljxCGIy3Cog+lvxB1l//U2ucMwxuy4W6s8bxBscIxjoo9Fqq5544cxBA1K4Dsv1rB9z4g8HdD66ViCoXkM5Ni/ rsa-key-20250731
```
Но из всего этого текста вот этот кусок является ключом:

```
AAAAB3NzaC1yc2EAAAADAQABAAABAQCSPH0v/sZhlXGnkHP9ezA/0xRp60JFHWv9onc9kbmUXhkcN9KwwfexXecDndZkH/xTubfoZUpqXKMHRVeg2fnjytkCNF/xYMrmLuus/ob7YKLE5dA7I4WNpw/0RsSlJz8fvDbv/OHme9PPpX0lpEAMxAQ1kjYN92R2gJAQHX0T9bvHGEO4UKCxl4xDIdHUW9H6vplOiRUjwuLurxuqYx5LLdRpAS9sAM6+8Em5a7sWNIQ2lcJ/5z4BDpU0JOrBfCljxCGIy3Cog+lvxB1l//U2ucMwxuy4W6s8bxBscIxjoo9Fqq5544cxBA1K4Dsv1rB9z4g8HdD66ViCoXkM5Ni/
```

Ставим аддон в HA:
<span style='color:var(--mk-color-red)'>Terminal & SSH</span>
ИМЕННО ЭТОТ, ПРЯМ ДОСЛОВНО ВБИВАТЬ!
Открываем конфиг плагина и там в ключ авторизации вставляем наш ключ, без лишних приписок!

## Сама установка HACS
Вводим руками это команду в терминал аддона:
```
wget -O - https://get.hacs.xyz | bash -
```

Нажимаем ctrl+R чтобы отчистить кэш браузера и перезапускаем HA.

В интеграциях добавляем HACS и входим через гитхаб.
