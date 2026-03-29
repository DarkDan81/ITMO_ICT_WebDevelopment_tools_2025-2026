from collections.abc import Sequence

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.db import get_session, init_db
from app.models import (
    Category,
    CategoryCreate,
    CategoryRead,
    CategoryReadWithUser,
    CategoryUpdate,
    Operation,
    OperationCreate,
    OperationReadWithRelations,
    OperationTagLink,
    OperationUpdate,
    Tag,
    TagCreate,
    TagRead,
    TagReadWithAssignedAt,
    TagUpdate,
    User,
    UserCreate,
    UserRead,
    UserReadWithRelations,
    UserUpdate,
)

app = FastAPI(
    title="Personal Finance Service ORM",
    description="Вторая практика: FastAPI + SQLModel + PostgreSQL.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_user_or_404(user_id: int, session: Session) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_category_or_404(category_id: int, session: Session) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def get_tag_or_404(tag_id: int, session: Session) -> Tag:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


def get_operation_or_404(operation_id: int, session: Session) -> Operation:
    statement = (
        select(Operation)
        .where(Operation.id == operation_id)
        .options(
            selectinload(Operation.user),
            selectinload(Operation.category),
            selectinload(Operation.tags),
        )
    )
    operation = session.exec(statement).first()
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")
    return operation


def ensure_user_exists(user_id: int | None, session: Session) -> None:
    if user_id is None or not session.get(User, user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")


def ensure_category_exists(category_id: int | None, session: Session) -> None:
    if category_id is None or not session.get(Category, category_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category does not exist")


def ensure_tag_ids_exist(tag_ids: Sequence[int], session: Session) -> list[Tag]:
    tags = []
    for tag_id in tag_ids:
        tag = session.get(Tag, tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tag {tag_id} does not exist")
        tags.append(tag)
    return tags


def serialize_operation(operation: Operation, session: Session) -> OperationReadWithRelations:
    links = session.exec(
        select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)
    ).all()
    assigned_map = {link.tag_id: link.assigned_at for link in links}
    tags = [
        TagReadWithAssignedAt(
            id=tag.id,
            name=tag.name,
            assigned_at=assigned_map.get(tag.id),
        )
        for tag in operation.tags
    ]

    return OperationReadWithRelations(
        id=operation.id,
        title=operation.title,
        amount=operation.amount,
        operation_type=operation.operation_type,
        operation_date=operation.operation_date,
        description=operation.description,
        user_id=operation.user_id,
        category_id=operation.category_id,
        user=UserRead.model_validate(operation.user) if operation.user else None,
        category=CategoryRead.model_validate(operation.category) if operation.category else None,
        tags=tags,
    )


def update_operation_links(operation: Operation, tag_ids: Sequence[int], session: Session) -> None:
    existing_links = session.exec(
        select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)
    ).all()
    for link in existing_links:
        session.delete(link)
    session.flush()

    ensure_tag_ids_exist(tag_ids, session)
    for tag_id in tag_ids:
        session.add(OperationTagLink(operation_id=operation.id, tag_id=tag_id))


@app.get("/")
def hello() -> str:
    return "Hello, personal finance ORM service!"


@app.get("/users", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)) -> list[User]:
    return session.exec(select(User)).all()


@app.get("/users/{user_id}", response_model=UserReadWithRelations)
def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.categories))
    )
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: Session = Depends(get_session)) -> User:
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user: UserUpdate, session: Session = Depends(get_session)) -> User:
    db_user = get_user_or_404(user_id, session)
    user_data = user.model_dump(exclude_unset=True)
    if "email" in user_data and user_data["email"] != db_user.email:
        existing_user = session.exec(select(User).where(User.email == user_data["email"])).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_session)) -> Response:
    user = get_user_or_404(user_id, session)
    if user.categories or user.operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has related categories or operations and cannot be deleted",
        )
    session.delete(user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/categories", response_model=list[CategoryRead])
def get_categories(session: Session = Depends(get_session)) -> list[Category]:
    return session.exec(select(Category)).all()


@app.get("/categories/{category_id}", response_model=CategoryReadWithUser)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    statement = (
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.user))
    )
    category = session.exec(statement).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@app.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, session: Session = Depends(get_session)) -> Category:
    ensure_user_exists(category.user_id, session)
    db_category = Category.model_validate(category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, category: CategoryUpdate, session: Session = Depends(get_session)) -> Category:
    db_category = get_category_or_404(category_id, session)
    category_data = category.model_dump(exclude_unset=True)
    if "user_id" in category_data:
        ensure_user_exists(category_data["user_id"], session)

    for key, value in category_data.items():
        setattr(db_category, key, value)

    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: Session = Depends(get_session)) -> Response:
    category = get_category_or_404(category_id, session)
    if category.operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category has related operations and cannot be deleted",
        )
    session.delete(category)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/tags", response_model=list[TagRead])
def get_tags(session: Session = Depends(get_session)) -> list[Tag]:
    return session.exec(select(Tag)).all()


@app.get("/tags/{tag_id}", response_model=TagRead)
def get_tag(tag_id: int, session: Session = Depends(get_session)) -> Tag:
    return get_tag_or_404(tag_id, session)


@app.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(tag: TagCreate, session: Session = Depends(get_session)) -> Tag:
    existing_tag = session.exec(select(Tag).where(Tag.name == tag.name)).first()
    if existing_tag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag with this name already exists")

    db_tag = Tag.model_validate(tag)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


@app.patch("/tags/{tag_id}", response_model=TagRead)
def update_tag(tag_id: int, tag: TagUpdate, session: Session = Depends(get_session)) -> Tag:
    db_tag = get_tag_or_404(tag_id, session)
    tag_data = tag.model_dump(exclude_unset=True)
    if "name" in tag_data and tag_data["name"] != db_tag.name:
        existing_tag = session.exec(select(Tag).where(Tag.name == tag_data["name"])).first()
        if existing_tag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag with this name already exists")

    for key, value in tag_data.items():
        setattr(db_tag, key, value)

    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


@app.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, session: Session = Depends(get_session)) -> Response:
    tag = get_tag_or_404(tag_id, session)
    if tag.operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag is linked to operations and cannot be deleted",
        )
    session.delete(tag)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/operations", response_model=list[OperationReadWithRelations])
def get_operations(session: Session = Depends(get_session)) -> list[OperationReadWithRelations]:
    statement = select(Operation).options(
        selectinload(Operation.user),
        selectinload(Operation.category),
        selectinload(Operation.tags),
    )
    operations = session.exec(statement).all()
    return [serialize_operation(operation, session) for operation in operations]


@app.get("/operations/{operation_id}", response_model=OperationReadWithRelations)
def get_operation(operation_id: int, session: Session = Depends(get_session)) -> OperationReadWithRelations:
    operation = get_operation_or_404(operation_id, session)
    return serialize_operation(operation, session)


@app.post("/operations", response_model=OperationReadWithRelations, status_code=status.HTTP_201_CREATED)
def create_operation(operation: OperationCreate, session: Session = Depends(get_session)) -> OperationReadWithRelations:
    ensure_user_exists(operation.user_id, session)
    ensure_category_exists(operation.category_id, session)

    payload = operation.model_dump(exclude={"tag_ids"})
    db_operation = Operation.model_validate(payload)
    session.add(db_operation)
    session.commit()
    session.refresh(db_operation)

    update_operation_links(db_operation, operation.tag_ids, session)
    session.commit()

    created_operation = get_operation_or_404(db_operation.id, session)
    return serialize_operation(created_operation, session)


@app.patch("/operations/{operation_id}", response_model=OperationReadWithRelations)
def update_operation(
    operation_id: int,
    operation: OperationUpdate,
    session: Session = Depends(get_session),
) -> OperationReadWithRelations:
    db_operation = get_operation_or_404(operation_id, session)
    operation_data = operation.model_dump(exclude_unset=True, exclude={"tag_ids"})

    if "user_id" in operation_data:
        ensure_user_exists(operation_data["user_id"], session)
    if "category_id" in operation_data:
        ensure_category_exists(operation_data["category_id"], session)

    for key, value in operation_data.items():
        setattr(db_operation, key, value)

    session.add(db_operation)
    session.commit()
    session.refresh(db_operation)

    if operation.tag_ids is not None:
        update_operation_links(db_operation, operation.tag_ids, session)
        session.commit()

    updated_operation = get_operation_or_404(operation_id, session)
    return serialize_operation(updated_operation, session)


@app.delete("/operations/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(operation_id: int, session: Session = Depends(get_session)) -> Response:
    operation = get_operation_or_404(operation_id, session)
    links = session.exec(
        select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)
    ).all()
    for link in links:
        session.delete(link)
    session.delete(operation)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
