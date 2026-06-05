-- === НАСТРОЙКИ ===

local SERVER_URL = "http://127.0.0.1:8000/lamp"  -- куда ходим за состоянием
local POLL_INTERVAL = 0.5  -- как часто опрашиваем, сек


-- === INTERNET CARD ===

local inetCards = computer.getPCIDevices(classes.FINInternetCard)
local inet = inetCards[1]

if inet == nil then
    computer.panic("Internet Card не найдена! Вставь её в компьютер.")
end

print("Internet Card найдена:", inet)


-- === НАХОДИМ ЛАМПУ ===
-- Ищем первый LightSource на сети

local lights = component.proxy(component.findComponent(classes.LightSource))
local light = lights[1]

if light == nil then
    computer.panic("Не нашёл ни одной лампы (LightSource) в сети. Подключи свет к network pole.")
end

print("Нашёл лампу:", light)


-- === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: TRIM ===

local function trim(s)
    if s == nil then return nil end
    s = string.gsub(s, "^%s+", "")
    s = string.gsub(s, "%s+$", "")
    return s
end


-- === ОПРОС СЕРВЕРА ===

local function fetchLampState()
    -- делаем GET запрос к нашему FastAPI
    local req = inet:request(SERVER_URL, "GET", "")
    local code, body = req:await()

    if code ~= 200 then
        print("[HTTP] Ошибка, код:", code or "nil")
        return nil
    end

    body = trim(body or "")

    if body == "on" then
        return true
    elseif body == "off" then
        return false
    else
        print("[HTTP] Непонятный ответ:", body)
        return nil
    end
end


-- === ГЛАВНЫЙ ЦИКЛ ===

print("Стартуем, опрашиваем:", SERVER_URL)

local lastState = nil

while true do
    local state = fetchLampState()

    if state ~= nil and state ~= lastState then
        -- ЛОГИ
        if state then
            print("[LAMP] ВКЛ (on)")
        else
            print("[LAMP] ВЫКЛ (off)")
        end

        -- РЕАЛЬНО УПРАВЛЯЕМ ЛАМПОЙ
        -- у LightSource есть поле isLightEnabled
        light.isLightEnabled = state

        lastState = state
    end

    event.pull(POLL_INTERVAL)
end
