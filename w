views:
  - title: Home
    path: fan-temp-control
    cards:
      - graph: line
        type: sensor
        entity: sensor.orange_pi_cpu_temp
        detail: 2
        icon: mdi:expansion-card
        limits:
          min: 34
      - graph: line
        type: sensor
        entity: sensor.fan_pwm
        detail: 2
        name: Частота ШИМ куллера сервера (Fan RWM)
        limits:
          max: 1024
          min: 0
        icon: mdi:chart-histogram
      - graph: line
        type: sensor
        entity: sensor.fan_rps
        detail: 2
        icon: mdi:fan-chevron-up
        name: Скорость вращения куллера сервера (Fan RPS)
      - type: entities
        entities:
          - entity: number.max_pwm
            secondary_info: entity-id
          - entity: number.max_temperature
          - entity: number.min_pwm
          - entity: number.off_temperature
    visible:
      - user: acc451cba6884b03a9ef0f696e26fdce
  - type: sections
    path: ''
    sections:
      - path: fan-temp-control-1
        cards:
          - type: heading
            heading_style: title
            heading: Статистика сервера в реальном времени
            badges:
              - type: entity
                show_state: true
                show_icon: true
                entity: sensor.orange_pi_cpu_temp
                state_content: last_updated
                color: red
          - type: heading
            heading_style: subtitle
            heading: Состояние сервера
          - features:
              - type: trend-graph
                hours_to_show: 2
            type: custom:mushroom-template-card
            primary: Температура процессора
            secondary: |
              {{ states('sensor.orange_pi_cpu_temp') }} °C
            icon: >-
              {% if states('sensor.orange_pi_cpu_temp') in ['unavailable',
              'unknown', 'none'] %}
                mdi:thermometer-off
              {% elif states('sensor.orange_pi_cpu_temp') | float >
              states('input_number.critical_temperature_cpu_orangepi') | float
              %}
                mdi:thermometer-alert
              {% else %}
                mdi:thermometer
              {% endif %}
            entity: sensor.orange_pi_cpu_temp
            features_position: bottom
            grid_options:
              columns: 12
              rows: 2
            color: >-
              {% if states('sensor.orange_pi_cpu_temp') in ['unavailable',
              'unknown', 'none'] %}
                pink
              {% elif states('sensor.orange_pi_cpu_temp') | float >
              states('input_number.critical_temperature_cpu_orangepi') | float
              %}
                red
              {% else %}
                green
              {% endif %}
          - type: custom:mushroom-number-card
            entity: input_number.critical_temperature_cpu_orangepi
            fill_container: true
            name: Уведомление о Крит. °C
            grid_options:
              columns: 12
              rows: 1
            layout: horizontal
            icon_color: yellow
            secondary_info: state
            visibility:
              - condition: user
                users:
                  - d83116fa0aec436bac1b740fe87620b4
            hold_action:
              action: perform-action
              perform_action: input_number.set_value
              target:
                entity_id: input_number.critical_temperature_cpu_orangepi
              data:
                value: 55
          - type: heading
            heading_style: subtitle
            heading: Параметры кулера
          - features:
              - type: trend-graph
                hours_to_show: 2
            type: custom:mushroom-template-card
            primary: Частота ШИМ кулера
            secondary: |
              {{ states('sensor.fan_pwm') }} PWM
            icon: >-
              {% if states('sensor.fan_pwm') in ['unavailable', 'unknown',
              'none'] %}
                mdi:chart-line-off
              {% elif states('sensor.fan_pwm') | float < 5 %}
                mdi:alert-circle
              {% else %}
                mdi:chart-histogram
              {% endif %}
            entity: sensor.fan_pwm
            features_position: bottom
            grid_options:
              columns: 12
              rows: 2
            color: >-
              {% if states('sensor.fan_pwm') in ['unavailable', 'unknown',
              'none'] %}
                pink
              {% elif states('sensor.fan_pwm') | float < 5 %}
                red
              {% else %}
                blue
              {% endif %}
          - features:
              - type: trend-graph
                hours_to_show: 2
            type: custom:mushroom-template-card
            primary: Скорость вращения куллера
            secondary: |
              {{ states('sensor.fan_rps') }} RPS
            icon: >-
              {% if states('sensor.fan_rps') in ['unavailable', 'unknown',
              'none'] %}
                mdi:fan-off
              {% elif states('sensor.fan_rps') | float < 5 %}
                mdi:fan-alert
              {% else %}
                mdi:fan-chevron-up
              {% endif %}
            entity: sensor.fan_rps
            features_position: bottom
            grid_options:
              columns: 12
              rows: 2
            color: >-
              {% if states('sensor.fan_rps') in ['unavailable', 'unknown',
              'none'] %}
                pink
              {% elif states('sensor.fan_rps') | float < 5 %}
                red
              {% else %}
                teal
              {% endif %}
            badge_icon: >-
              {% if states('sensor.fan_rps') in ['unavailable', 'unknown',
              'none'] %}
                mdi:wifi-alert
              {% endif %}
        column_span: 1
      - type: grid
        cards:
          - type: heading
            heading_style: title
            heading: Настройки охлаждения
          - type: heading
            heading_style: subtitle
            heading: Пороги температур
          - type: custom:mushroom-number-card
            entity: number.max_temperature
            fill_container: true
            grid_options:
              columns: 12
              rows: 1
            layout: horizontal
            icon_color: green
            secondary_info: state
            visibility:
              - condition: user
                users:
                  - d83116fa0aec436bac1b740fe87620b4
            icon: mdi:thermometer-chevron-up
          - type: custom:mushroom-number-card
            fill_container: true
            grid_options:
              columns: 12
              rows: 1
            layout: horizontal
            icon_color: green
            secondary_info: state
            visibility:
              - condition: user
                users:
                  - d83116fa0aec436bac1b740fe87620b4
            entity: number.off_temperature
            icon: mdi:thermometer-chevron-down
            name: Temp для 0% вращения
          - type: heading
            heading_style: subtitle
            heading: Пороги ШИМ
          - type: custom:mushroom-number-card
            entity: number.max_pwm
            fill_container: true
            grid_options:
              columns: 12
              rows: 1
            layout: horizontal
            icon_color: blue
            secondary_info: state
            visibility:
              - condition: user
                users:
                  - d83116fa0aec436bac1b740fe87620b4
            icon: mdi:boom-gate-arrow-up
          - type: custom:mushroom-number-card
            entity: number.min_pwm
            fill_container: true
            grid_options:
              columns: 12
              rows: 1
            layout: horizontal
            icon_color: blue
            secondary_info: state
            visibility:
              - condition: user
                users:
                  - d83116fa0aec436bac1b740fe87620b4
            icon: mdi:boom-gate-arrow-down
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: automation.sbrosit_vse_nastroiki_pwm_u_kulera_po_umolchaniiu
            name: Настройки по умолчанию
            grid_options:
              columns: 6
              rows: auto
            icon: mdi:file-download
            scrolling_effect: false
            show_icon: true
            force_icon: false
            show_name: true
            show_state: false
            show_last_changed: false
            show_attribute: false
            show_last_updated: false
            button_action:
              tap_action:
                action: perform-action
                target:
                  entity_id: automation.sbrosit_vse_nastroiki_pwm_u_kulera_po_umolchaniiu
                perform_action: automation.trigger
                data:
                  skip_condition: true
            sub_button: []
            card_layout: normal
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: automation.sbrosit_vse_nastroiki_pwm_u_kulera_po_umolchaniiu
            name: Настройки "тихий режим"
            grid_options:
              columns: 6
              rows: auto
            icon: mdi:file-download
            scrolling_effect: false
            show_icon: true
            force_icon: false
            show_name: true
            show_state: false
            show_last_changed: false
            show_attribute: false
            show_last_updated: false
            button_action:
              tap_action:
                action: perform-action
                target:
                  entity_id: automation.sbrosit_vse_nastroiki_pwm_u_kulera_po_umolchaniiu
                perform_action: automation.trigger
                data:
                  skip_condition: true
            sub_button: []
            card_layout: normal
      - type: grid
        cards:
          - type: heading
            heading_style: title
            heading: Системная статистика
            icon: mdi:server
          - type: custom:bubble-card
            card_type: empty-column
          - features:
              - type: trend-graph
                hours_to_show: 3
                min_y: 0
                max_y: 100
            type: custom:mushroom-template-card
            secondary: |
              {{ states('sensor.system_monitor_processor_use') }}%
            icon: >-
              {% if states('sensor.fan_pwm') in ['unavailable', 'unknown',
              'none'] %}
                mdi:chart-line-off
              {% elif states('sensor.fan_pwm') | float < 5 %}
                mdi:alert-circle
              {% else %}
                mdi:chart-histogram
              {% endif %}
            features_position: bottom
            grid_options:
              columns: 12
              rows: 2
            entity: sensor.system_monitor_processor_use
            primary: CPU использование
            color: pink
          - show_name: true
            show_icon: true
            show_state: true
            type: glance
            entities:
              - entity: sensor.system_monitor_memory_use
              - entity: sensor.system_monitor_memory_free
            state_color: false
            theme: Graphite Light
            columns: 2
            grid_options:
              columns: 9
              rows: auto
          - type: vertical-stack
            cards: []
    max_columns: 4
    title: Панель управления охлаждением
    icon: mdi:view-dashboard-variant
    cards: []
    theme: Graphite Light
    badges: []
    dense_section_placement: false
