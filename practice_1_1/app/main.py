from fastapi import FastAPI, HTTPException, Response, status

from app.models import Category, CategoryCreate, Operation, OperationCreate, OperationType, Tag

app = FastAPI(
    title="Personal Finance Service",
    description="Учебное FastAPI-приложение для учета личных финансов.",
    version="1.0.0",
)


categories_db: list[Category] = [
    Category(id=1, name="Salary", monthly_limit=None),
    Category(id=2, name="Food", monthly_limit=25000),
    Category(id=3, name="Transport", monthly_limit=8000),
]

operations_db: list[Operation] = [
    Operation(
        id=1,
        title="March salary",
        amount=120000,
        operation_type=OperationType.income,
        operation_date="2026-03-10",
        category=categories_db[0],
        tags=[Tag(id=1, name="work"), Tag(id=2, name="main-income")],
        description="Monthly salary payment",
    ),
    Operation(
        id=2,
        title="Groceries",
        amount=5400,
        operation_type=OperationType.expense,
        operation_date="2026-03-14",
        category=categories_db[1],
        tags=[Tag(id=3, name="family"), Tag(id=4, name="supermarket")],
        description="Weekly grocery shopping",
    ),
    Operation(
        id=3,
        title="Metro card top-up",
        amount=2300,
        operation_type=OperationType.expense,
        operation_date="2026-03-16",
        category=categories_db[2],
        tags=[Tag(id=5, name="city"), Tag(id=6, name="commute")],
        description="Public transport for the month",
    ),
]


def get_next_operation_id() -> int:
    return max((operation.id for operation in operations_db), default=0) + 1


def get_next_category_id() -> int:
    return max((category.id for category in categories_db), default=0) + 1


def get_next_tag_id() -> int:
    max_existing_tag = max(
        (tag.id for operation in operations_db for tag in operation.tags),
        default=0,
    )
    return max_existing_tag + 1


def find_operation_index(operation_id: int) -> int | None:
    for index, operation in enumerate(operations_db):
        if operation.id == operation_id:
            return index
    return None


def find_category_index(category_id: int) -> int | None:
    for index, category in enumerate(categories_db):
        if category.id == category_id:
            return index
    return None


def build_operation(operation_in: OperationCreate, operation_id: int) -> Operation:
    next_tag_id = get_next_tag_id()
    tags = []
    for offset, tag in enumerate(operation_in.tags):
        tags.append(Tag(id=next_tag_id + offset, name=tag.name))

    return Operation(
        id=operation_id,
        title=operation_in.title,
        amount=operation_in.amount,
        operation_type=operation_in.operation_type,
        operation_date=operation_in.operation_date,
        category=operation_in.category,
        tags=tags,
        description=operation_in.description,
    )


@app.get("/")
def hello() -> str:
    return "Hello, personal finance service!"


@app.get("/operations", response_model=list[Operation])
def get_operations() -> list[Operation]:
    return operations_db


@app.get("/operations/{operation_id}", response_model=Operation)
def get_operation(operation_id: int) -> Operation:
    operation_index = find_operation_index(operation_id)
    if operation_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")
    return operations_db[operation_index]


@app.post("/operations", response_model=Operation, status_code=status.HTTP_201_CREATED)
def create_operation(operation: OperationCreate) -> Operation:
    created_operation = build_operation(operation, get_next_operation_id())
    operations_db.append(created_operation)
    return created_operation


@app.put("/operations/{operation_id}", response_model=Operation)
def update_operation(operation_id: int, operation: OperationCreate) -> Operation:
    operation_index = find_operation_index(operation_id)
    if operation_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")

    updated_operation = build_operation(operation, operation_id)
    operations_db[operation_index] = updated_operation
    return updated_operation


@app.delete("/operations/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(operation_id: int) -> Response:
    operation_index = find_operation_index(operation_id)
    if operation_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")

    operations_db.pop(operation_index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/categories", response_model=list[Category])
def get_categories() -> list[Category]:
    return categories_db


@app.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: int) -> Category:
    category_index = find_category_index(category_id)
    if category_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return categories_db[category_index]


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate) -> Category:
    created_category = Category(id=get_next_category_id(), **category.model_dump())
    categories_db.append(created_category)
    return created_category


@app.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: int, category: CategoryCreate) -> Category:
    category_index = find_category_index(category_id)
    if category_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    updated_category = Category(id=category_id, **category.model_dump())
    categories_db[category_index] = updated_category

    for index, operation in enumerate(operations_db):
        if operation.category.id == category_id:
            operations_db[index] = operation.model_copy(update={"category": updated_category})

    return updated_category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int) -> Response:
    category_index = find_category_index(category_id)
    if category_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for operation in operations_db:
        if operation.category.id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is used in operations and cannot be deleted",
            )

    categories_db.pop(category_index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
