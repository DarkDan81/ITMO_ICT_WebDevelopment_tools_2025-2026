from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models import (Category, CategoryCreate, CategoryRead, CategoryReadWithUser, CategoryUpdate,
                        Operation, OperationCreate, OperationReadWithRelations, OperationTagLink,
                        OperationUpdate, Tag, TagCreate, TagRead, TagReadWithMetadata, TagUpdate, User, UserRead)
from app.security import get_current_user

router = APIRouter(tags=["Финансы"])


def owned(model, item_id: int, user: User, session: Session):
    item = session.get(model, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(404, "Запись не найдена")
    return item


def check_owner(user_id: int | None, user: User) -> None:
    if user_id is not None and user_id != user.id:
        raise HTTPException(403, "Нельзя указать другого владельца")


def check_tags(assignments, session: Session) -> None:
    for assignment in assignments:
        if session.get(Tag, assignment.tag_id) is None:
            raise HTTPException(400, f"Тег {assignment.tag_id} не найден")


def set_tags(operation: Operation, assignments, session: Session) -> None:
    for link in session.exec(select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)).all():
        session.delete(link)
    session.flush()
    for tag in assignments:
        session.add(OperationTagLink(operation_id=operation.id, tag_id=tag.tag_id, priority=tag.priority))


def serialize_operation(operation: Operation, session: Session) -> OperationReadWithRelations:
    links = session.exec(select(OperationTagLink).where(OperationTagLink.operation_id == operation.id)).all()
    tags = []
    for link in links:
        tag = session.get(Tag, link.tag_id)
        tags.append(TagReadWithMetadata(id=tag.id, name=tag.name, assigned_at=link.assigned_at, priority=link.priority))
    return OperationReadWithRelations(
        **operation.model_dump(), user=UserRead.model_validate(operation.user),
        category=CategoryRead.model_validate(operation.category), tags=tags,
    )


@router.get("/categories", response_model=list[CategoryRead])
def categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[Category]:
    return list(session.exec(select(Category).where(Category.user_id == user.id)).all())


@router.get("/categories/{category_id}", response_model=CategoryReadWithUser)
def category(category_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Category:
    return owned(Category, category_id, user, session)


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(data: CategoryCreate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Category:
    check_owner(data.user_id, user)
    item = Category.model_validate(data.model_dump() | {"user_id": user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, data: CategoryUpdate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Category:
    item = owned(Category, category_id, user, session)
    check_owner(data.user_id, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)) -> Response:
    item = owned(Category, category_id, user, session)
    if item.operations:
        raise HTTPException(409, "Категория используется в операциях")
    session.delete(item)
    session.commit()
    return Response(status_code=204)


# Теги — общий справочник. Личные суммы и категории доступны только владельцу.
@router.get("/tags", response_model=list[TagRead])
def tags(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[Tag]:
    return list(session.exec(select(Tag)).all())


def get_tag(tag_id: int, session: Session) -> Tag:
    item = session.get(Tag, tag_id)
    if item is None:
        raise HTTPException(404, "Тег не найден")
    return item


@router.get("/tags/{tag_id}", response_model=TagRead)
def tag(tag_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Tag:
    return get_tag(tag_id, session)


def save_tag(item: Tag, session: Session) -> Tag:
    session.add(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Тег с таким именем уже существует")
    session.refresh(item)
    return item


@router.post("/tags", response_model=TagRead, status_code=201)
def create_tag(data: TagCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Tag:
    return save_tag(Tag.model_validate(data), session)


@router.patch("/tags/{tag_id}", response_model=TagRead)
def update_tag(tag_id: int, data: TagUpdate, user: User = Depends(get_current_user),
               session: Session = Depends(get_session)) -> Tag:
    item = get_tag(tag_id, session)
    if any(operation.user_id != user.id for operation in item.operations):
        raise HTTPException(409, "Тег используется другим пользователем")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    return save_tag(item, session)


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Response:
    item = get_tag(tag_id, session)
    if item.operations:
        raise HTTPException(409, "Тег используется в операциях")
    session.delete(item)
    session.commit()
    return Response(status_code=204)


@router.get("/operations", response_model=list[OperationReadWithRelations])
def operations(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> list[OperationReadWithRelations]:
    items = session.exec(select(Operation).where(Operation.user_id == user.id)).all()
    return [serialize_operation(item, session) for item in items]


@router.get("/operations/{operation_id}", response_model=OperationReadWithRelations)
def operation(operation_id: int, user: User = Depends(get_current_user),
              session: Session = Depends(get_session)) -> OperationReadWithRelations:
    return serialize_operation(owned(Operation, operation_id, user, session), session)


@router.post("/operations", response_model=OperationReadWithRelations, status_code=201)
def create_operation(data: OperationCreate, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> OperationReadWithRelations:
    check_owner(data.user_id, user)
    if data.category_id is None:
        raise HTTPException(422, "Нужно указать category_id")
    owned(Category, data.category_id, user, session)
    check_tags(data.tags, session)
    item = Operation.model_validate(data.model_dump(exclude={"tags"}) | {"user_id": user.id})
    session.add(item)
    session.flush()  # Получаем id, но ещё не фиксируем операцию.
    set_tags(item, data.tags, session)
    session.commit()  # Операция и её теги сохраняются вместе.
    session.refresh(item)
    return serialize_operation(item, session)


@router.patch("/operations/{operation_id}", response_model=OperationReadWithRelations)
def update_operation(operation_id: int, data: OperationUpdate, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> OperationReadWithRelations:
    item = owned(Operation, operation_id, user, session)
    check_owner(data.user_id, user)
    if data.category_id is not None:
        owned(Category, data.category_id, user, session)
    if data.tags is not None:
        check_tags(data.tags, session)
    for key, value in data.model_dump(exclude_unset=True, exclude={"tags"}).items():
        setattr(item, key, value)
    session.add(item)
    if data.tags is not None:
        set_tags(item, data.tags, session)
    session.commit()
    session.refresh(item)
    return serialize_operation(item, session)


@router.delete("/operations/{operation_id}", status_code=204)
def delete_operation(operation_id: int, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)) -> Response:
    item = owned(Operation, operation_id, user, session)
    item.tags = []
    session.delete(item)
    session.commit()
    return Response(status_code=204)
