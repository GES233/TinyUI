""" `tinyui.application.base`
    ~~~~

    This package is a simple demostration for the core part 
    of Clean Architecture, and it provides some basic 
    components for it.

    ```text
    +-----------Application-----------+
    |   Application Service(Usecase)  |
    |      +------Domain------+       |
    |      |  Domain Service  |    <==DTO==> Outside
    |      | +--------------+ |       |
    |      | | Domain Model <-interface----> implementation
    |      | +--------------+ |       |
    |      +------------------+       |
    +---------------------------------+
    ```

    (external part are not shown in the illustrate)

    - - -

    Domain Model
    ~~~~~~~~

    Provides some models to contain the objects of business:

    - Entity
      - AggregateRoot
    - VO(Value object)
    - Domain Service

    Domain Service
    ~~~~~~~~

    Provides some functions of domain models.

    Usecase(Application Service)
    ~~~~~~~~

    ...

"""
