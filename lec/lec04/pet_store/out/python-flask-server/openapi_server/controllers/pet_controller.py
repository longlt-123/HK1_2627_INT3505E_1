import flask
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.modify_petwith_id_request import ModifyPetwithIDRequest  # noqa: E501
from openapi_server.models.pet import Pet  # noqa: E501
from openapi_server.models.pets_post400_response import PetsPost400Response  # noqa: E501
from openapi_server import util


def delete_petwith_id(pet_id):  # noqa: E501
    """Xóa thú cưng theo ID

     # noqa: E501

    :param pet_id: ID của thú cưng
    :type pet_id: int

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pets():  # noqa: E501
    """Lấy danh sách toàn bộ thú cưng

     # noqa: E501


    :rtype: Union[List[Pet], Tuple[List[Pet], int], Tuple[List[Pet], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_petwith_id(pet_id):  # noqa: E501
    """Lấy thông tin chi tiết một thú cưng theo ID

     # noqa: E501

    :param pet_id: ID của thú cưng
    :type pet_id: int

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    return 'do some magic!'


def modify_petwith_id(pet_id, body):  # noqa: E501
    """Sửa đổi thông tin của thú cưng

     # noqa: E501

    :param pet_id: ID của thú cưng
    :type pet_id: int
    :param modify_petwith_id_request: 
    :type modify_petwith_id_request: dict | bytes

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    modify_petwith_id_request = body
    if flask.request.is_json:
        modify_petwith_id_request = ModifyPetwithIDRequest.from_dict(flask.request.get_json())  # noqa: E501
    return 'do some magic!'


def pets_pet_id_put(pet_id, body):  # noqa: E501
    """Cập nhật thông tin thú cưng

    Ghi đè thông tin cũ bằng một Object Pet hoàn toàn mới. # noqa: E501

    :param pet_id: ID của thú cưng
    :type pet_id: int
    :param pet: 
    :type pet: dict | bytes

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    pet = body
    if flask.request.is_json:
        pet = Pet.from_dict(flask.request.get_json())  # noqa: E501
    return 'do some magic!'


def pets_post(body):  # noqa: E501
    """Thêm thú cưng mới

     # noqa: E501

    :param pet: 
    :type pet: dict | bytes

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    pet = body
    if flask.request.is_json:
        pet = Pet.from_dict(flask.request.get_json())  # noqa: E501
    return 'do some magic!'
