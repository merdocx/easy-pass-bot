# Архитектура системы

## Обзор

Easy Pass Bot построен на современной архитектуре с использованием принципов Clean Architecture, SOLID и Domain-Driven Design.

## Диаграмма архитектуры

```mermaid
graph TB
    subgraph "Пользователи"
        U1[👥 Жители]
        U2[🛡️ Охранники]
        U3[👑 Администраторы]
    end
    
    subgraph "Telegram API"
        TG[Telegram Bot API]
    end
    
    subgraph "Easy Pass Bot"
        subgraph "Presentation Layer"
            H1[Resident Handlers]
            H2[Security Handlers]
            H3[Admin Handlers]
            H4[Common Handlers]
        end
        
        subgraph "Application Layer"
            S1[User Service]
            S2[Pass Service]
            S3[Validation Service]
            S4[Notification Service]
        end
        
        subgraph "Domain Layer"
            M1[User Model]
            M2[Pass Model]
            E1[Business Logic]
        end
        
        subgraph "Infrastructure Layer"
            D1[Database]
            C1[Cache Service]
            M3[Metrics]
            A1[Audit Logger]
        end
    end
    
    subgraph "External Services"
        DB[(SQLite Database)]
        LOG[Log Files]
        METRICS[Metrics Storage]
    end
    
    U1 --> TG
    U2 --> TG
    U3 --> TG
    TG --> H1
    TG --> H2
    TG --> H3
    TG --> H4
    
    H1 --> S1
    H2 --> S2
    H3 --> S1
    H4 --> S3
    
    S1 --> M1
    S2 --> M2
    S3 --> E1
    S4 --> E1
    
    S1 --> D1
    S2 --> D1
    S3 --> C1
    S4 --> M3
    
    D1 --> DB
    M3 --> METRICS
    A1 --> LOG
```

## Слои архитектуры

### 1. Presentation Layer (Слой представления)

**Назначение**: Обработка входящих сообщений от Telegram API

**Компоненты**:
- `ResidentHandlers` - обработчики для жителей
- `SecurityHandlers` - обработчики для охранников
- `AdminHandlers` - обработчики для администраторов
- `CommonHandlers` - общие обработчики

**Принципы**:
- Тонкий слой, только маршрутизация
- Валидация входных данных
- Преобразование в доменные объекты

### 2. Application Layer (Слой приложения)

**Назначение**: Координация бизнес-логики и оркестрация сервисов

**Компоненты**:
- `UserService` - управление пользователями
- `PassService` - управление пропусками
- `ValidationService` - валидация данных
- `NotificationService` - отправка уведомлений

**Принципы**:
- Содержит бизнес-логику приложения
- Координирует доменные сервисы
- Управляет транзакциями

### 3. Domain Layer (Доменный слой)

**Назначение**: Содержит основную бизнес-логику и доменные модели

**Компоненты**:
- `User` - модель пользователя
- `Pass` - модель пропуска
- `Business Logic` - правила бизнеса
- `Domain Events` - доменные события

**Принципы**:
- Независим от внешних зависимостей
- Содержит чистую бизнес-логику
- Определяет интерфейсы для внешних сервисов

### 4. Infrastructure Layer (Слой инфраструктуры)

**Назначение**: Реализация внешних зависимостей и технических деталей

**Компоненты**:
- `Database` - работа с базой данных
- `CacheService` - кэширование
- `Metrics` - сбор метрик
- `AuditLogger` - аудит действий

**Принципы**:
- Реализует интерфейсы доменного слоя
- Содержит технические детали
- Изолирован от бизнес-логики

## Диаграмма компонентов

```mermaid
graph LR
    subgraph "Core"
        I1[Interfaces]
        E1[Exceptions]
        B1[Base Classes]
        C1[Container]
    end
    
    subgraph "Services"
        S1[User Service]
        S2[Pass Service]
        S3[Validation Service]
        S4[Notification Service]
    end
    
    subgraph "Security"
        R1[Rate Limiter]
        V1[Validator]
        A1[Audit Logger]
    end
    
    subgraph "Monitoring"
        M1[Metrics Collector]
        H1[Health Checker]
        A2[Alerting]
    end
    
    subgraph "Features"
        AN[Analytics]
        N[Navigation]
        C[Confirmation]
    end
    
    I1 --> S1
    I1 --> S2
    I1 --> S3
    I1 --> S4
    
    S1 --> R1
    S2 --> V1
    S3 --> A1
    
    S1 --> M1
    S2 --> H1
    S3 --> A2
    
    S1 --> AN
    S2 --> N
    S3 --> C
```

## Диаграмма последовательности

### Создание пропуска

```mermaid
sequenceDiagram
    participant U as User
    participant H as Handler
    participant VS as ValidationService
    participant PS as PassService
    participant DB as Database
    participant NS as NotificationService
    
    U->>H: Подача заявки на пропуск
    H->>VS: Валидация данных
    VS-->>H: Данные валидны
    H->>PS: Создание пропуска
    PS->>DB: Сохранение в БД
    DB-->>PS: Пропуск создан
    PS->>NS: Уведомление пользователя
    NS-->>U: Уведомление о создании
    PS-->>H: Пропуск создан
    H-->>U: Подтверждение
```

### Поиск пропуска

```mermaid
sequenceDiagram
    participant S as Security
    participant H as Handler
    participant VS as ValidationService
    participant PS as PassService
    participant DB as Database
    
    S->>H: Поиск пропуска
    H->>VS: Валидация запроса
    VS-->>H: Запрос валиден
    H->>PS: Поиск пропуска
    PS->>DB: Запрос к БД
    DB-->>PS: Результаты поиска
    PS-->>H: Найденные пропуски
    H-->>S: Список пропусков
```

## Диаграмма базы данных

```mermaid
erDiagram
    USERS {
        int id PK
        int telegram_id UK
        string role
        string full_name
        string phone_number
        string apartment
        string status
        datetime created_at
        datetime updated_at
    }
    
    PASSES {
        int id PK
        int user_id FK
        string car_number
        string status
        datetime created_at
        datetime used_at
        int used_by_id FK
    }
    
    USERS ||--o{ PASSES : creates
    USERS ||--o{ PASSES : uses
```

## Диаграмма развертывания

```mermaid
graph TB
    subgraph "Production Server"
        subgraph "Application Layer"
            BOT[Easy Pass Bot]
            NGINX[Nginx Reverse Proxy]
        end
        
        subgraph "Data Layer"
            DB[(SQLite Database)]
            LOGS[Log Files]
            CACHE[Cache Storage]
        end
        
        subgraph "Monitoring"
            PROM[Prometheus]
            GRAF[Grafana]
            ALERT[Alert Manager]
        end
    end
    
    subgraph "External Services"
        TG[Telegram API]
        USERS[Users]
    end
    
    USERS --> TG
    TG --> NGINX
    NGINX --> BOT
    BOT --> DB
    BOT --> LOGS
    BOT --> CACHE
    BOT --> PROM
    PROM --> GRAF
    PROM --> ALERT
```

## Принципы проектирования

### 1. SOLID принципы

**Single Responsibility Principle (SRP)**
- Каждый класс имеет одну ответственность
- `UserService` - только управление пользователями
- `PassService` - только управление пропусками

**Open/Closed Principle (OCP)**
- Код открыт для расширения, закрыт для модификации
- Новые типы валидации через наследование
- Новые типы уведомлений через интерфейсы

**Liskov Substitution Principle (LSP)**
- Подклассы могут заменять базовые классы
- Все сервисы реализуют свои интерфейсы
- Все валидаторы наследуют от `BaseValidator`

**Interface Segregation Principle (ISP)**
- Интерфейсы разделены по функциональности
- `IUserService` - только для пользователей
- `IPassService` - только для пропусков

**Dependency Inversion Principle (DIP)**
- Зависимость от абстракций, не от конкретных классов
- Использование интерфейсов
- Dependency Injection контейнер

### 2. Clean Architecture

**Независимость от фреймворков**
- Бизнес-логика не зависит от aiogram
- Можно заменить Telegram на другой мессенджер

**Тестируемость**
- Каждый компонент можно тестировать изолированно
- Использование моков и стабов

**Независимость от UI**
- Логика не привязана к Telegram интерфейсу
- Можно добавить веб-интерфейс

**Независимость от базы данных**
- Бизнес-логика не зависит от SQLite
- Можно заменить на PostgreSQL

### 3. Domain-Driven Design

**Ubiquitous Language**
- Общие термины для всех участников
- `User`, `Pass`, `Resident`, `Security`, `Admin`

**Bounded Contexts**
- Четкие границы между доменами
- Отдельные модели для разных контекстов

**Aggregates**
- `User` - агрегат пользователя
- `Pass` - агрегат пропуска

## Паттерны проектирования

### 1. Repository Pattern

```python
class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create(self, user: User) -> int:
        pass
```

### 2. Service Layer Pattern

```python
class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    async def create_user(self, **kwargs) -> User:
        # Бизнес-логика
        pass
```

### 3. Dependency Injection

```python
@inject('user_service')
class UserHandler:
    def __init__(self, user_service: IUserService):
        self.user_service = user_service
```

### 4. Observer Pattern

```python
class EventBus:
    def __init__(self):
        self.observers = []
    
    def subscribe(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.handle(event)
```

### 5. Factory Pattern

```python
class ServiceFactory:
    @staticmethod
    def create_user_service() -> IUserService:
        user_repo = UserRepository()
        notification_service = NotificationService()
        return UserService(user_repo, notification_service)
```

## Масштабирование

### Горизонтальное масштабирование

1. **Load Balancer** - распределение нагрузки
2. **Multiple Instances** - несколько экземпляров бота
3. **Shared Database** - общая база данных
4. **Message Queue** - очередь сообщений

### Вертикальное масштабирование

1. **More CPU** - больше процессорных ядер
2. **More RAM** - больше оперативной памяти
3. **SSD Storage** - быстрый диск
4. **Network Optimization** - оптимизация сети

## Мониторинг и наблюдаемость

### Метрики

- **Business Metrics** - бизнес-метрики
- **Technical Metrics** - технические метрики
- **Performance Metrics** - метрики производительности

### Логирование

- **Structured Logging** - структурированные логи
- **Log Levels** - уровни логирования
- **Log Aggregation** - агрегация логов

### Трассировка

- **Distributed Tracing** - распределенная трассировка
- **Request Tracing** - трассировка запросов
- **Performance Tracing** - трассировка производительности

## Безопасность

### Аутентификация и авторизация

- **JWT Tokens** - токены для API
- **Role-Based Access** - доступ на основе ролей
- **Permission Matrix** - матрица разрешений

### Защита данных

- **Encryption at Rest** - шифрование в покое
- **Encryption in Transit** - шифрование в передаче
- **Data Masking** - маскирование данных

### Аудит

- **Audit Logging** - логирование аудита
- **Compliance** - соответствие требованиям
- **Data Retention** - хранение данных

## Заключение

Архитектура Easy Pass Bot спроектирована с учетом современных принципов разработки, обеспечивая:

- **Масштабируемость** - легко добавлять новые функции
- **Тестируемость** - каждый компонент тестируется изолированно
- **Поддерживаемость** - код легко понимать и изменять
- **Производительность** - оптимизированная работа
- **Безопасность** - защита данных и пользователей

Эта архитектура позволяет системе расти и развиваться вместе с потребностями пользователей.





