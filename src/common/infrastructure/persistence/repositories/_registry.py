from src.common.application.ports.repository import RepositoryType, IRepository


repositories_list: dict[RepositoryType, type[IRepository]] = {}
