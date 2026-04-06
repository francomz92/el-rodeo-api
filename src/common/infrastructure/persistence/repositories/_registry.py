from src.common.application.ports.repository import IRepository
from src.auth.infrastructure.persistance.repositories.users import UserRepository, IUserRepository


repositories_list: dict[type[IRepository], type[IRepository]] = {
    IUserRepository: UserRepository,
}
