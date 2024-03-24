
# Бизнес-кейс «Processing supermarket promotions data»

Самостоятельная работа

7.1.1. Развернуть ВМ [ubuntu_mgpu.ova](https://disk.yandex.ru/d/Psofa9xtbgUEOw) в [VirtualBox](https://disk.yandex.ru/d/3fD00plnL_a4Cw).

7.1.2. Клонировать на ПК задание **Бизнес-кейс «Processing supermarket promotions data»** в домашний каталог ВМ. 

`git clone https://github.com/BosenkoTM/workshop-on-ETL.git`

7.1.3. Запустить контейнер с **Бизнес-кейсом «Processing supermarket promotions data»**, изучить  основные элементы `DAG` в `Apache Airflow`. 
   - Создать триггер `DAG` согласно алгоритму, который предоставит преподаватель.
   - Изучить логи, выполненного триггера `DAG`. Скачать логи из контейнера в основную ОС.

**7.1.4.** Агрегированные данные бизнес-процесса, полученные в результате работы `DAG` в `Apache Airflow`, выгрузить в `Postgr SQL`. 

71.5. Спроектировать верхнеуровневую архитектуру аналитического решения **Бизнес-кейса «Processing supermarket promotions data»** в `draw.io`. Необходимо использовать:
   - `Source Layer` - слой источников данных.
   - `Storage Layer` - слой хранения данных.
   - `Business Layer` - слой для доступа к данным пользователей.

7.1.6. Спроектировать архитектуру триггера `DAG` **Бизнес-кейса «Processing supermarket promotions data»** в `draw.io`. Необходимо использовать:
   - `Source Layer` - слой источников данных.
   - `Storage Layer` - слой хранения данных.
   - `Business Layer` - слой для доступа к данным пользователей.

7.1.7. Построить диаграмму Ганта работы `DAG` в `Apache Airflow`.

7.1.8. Результаты исследований представить в виде файла `ФИО-07.pdf`, в котором отражены следующие результаты:
- постановка задачи;
- исходный код всех DAGs, которые требовались для решения задачи, а также представить граф `DAG` в `Apache Airflow`;
- верхнеуровневая архитектура задания **Бизнес-кейса «Processing supermarket promotions data»**, выполненная в `draw.io`;
- архитектура `DAG` **Бизнес-кейса «Processing supermarket promotions data»** , выполненная в `draw.io`;
- диаграмма Ганта `DAG` в `Apache Airflow`;
- Описание DAGs триггеров. 

После проверки преподавателем работоспособности триггеров `DAG`, выгрузить отчет на портал [moodle]().


## Использование

Чтобы начать работу с примерами кода, запустите `Airflow` с помощью `Docker Compose`, выполнив команду:

Для версии `v1`:

```bash
docker-compose up -d
```
Для версии `v2`:

```bash
docker compose up -d
```

Веб-сервер инициализирует несколько задач, поэтому подождите несколько секунд, после чего сможете получить доступ к веб-серверу Airflow по адресу http://localhost:8080.

Чтобы остановить выполнение примеров, выполните следующую команду:

Для версии `v1`:

```bash
docker-compose down -v
```
Для версии `v2`:

```bash
docker compose down -v
```