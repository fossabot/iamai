"""CQHTTP 适配器事件。"""
import inspect
from typing import TYPE_CHECKING, Any, Dict, Type, Union, Literal, TypeVar, Optional

from pydantic import Field, BaseModel

from iamai.event import Event

from .message import CQHTTPMessage

if TYPE_CHECKING:
    from . import CQHTTPAdapter
    from .message import T_CQMSG

T_CQHTTPEvent = TypeVar("T_CQHTTPEvent", bound="CQHTTPEvent")


class Sender(BaseModel):
    user_id: Optional[int]
    nickname: Optional[str]
    card: Optional[str]
    sex: Optional[Literal["male", "female", "unknown"]]
    age: Optional[int]
    area: Optional[str]
    level: Optional[str]
    role: Optional[str]
    title: Optional[str]


class Anonymous(BaseModel):
    id: int
    name: str
    flag: str


class File(BaseModel):
    id: str
    name: str
    size: int
    busid: int


class OfflineFile(BaseModel):
    name: str
    size: int
    url: str


class Device(BaseModel):
    app_id: int
    device_name: str
    device_kind: str


class Status(BaseModel):
    online: bool
    good: bool

    class Config:
        extra = "allow"


class ReactionInfo(BaseModel):
    """当前消息被贴表情列表"""

    emoji_id: Optional[str]
    emoji_index: Optional[int]
    emoji_type: Optional[int]
    emoji_name: Optional[str]
    count: Optional[int]
    clicked: Optional[bool]


class ChannelInfo(BaseModel):
    pass


class CQHTTPEvent(Event["CQHTTPAdapter"]):
    """CQHTTP 事件基类"""

    __event__ = ""
    type: Optional[str] = Field(alias="post_type")
    time: int
    self_id: int
    self_tiny_id: Optional[str]
    post_type: Literal["message", "message_sent", "notice", "request", "meta_event"]

    @property
    def to_me(self) -> bool:
        """当前事件的 user_id 是否等于 self_id 或 self_tiny_id。"""
        return getattr(self, "user_id") in [self.self_id, self.self_tiny_id]


class MessageEvent(CQHTTPEvent):
    """消息事件"""

    __event__ = "message"
    post_type: Literal["message"]
    message_type: Literal["private", "group", "guild"]
    sub_type: Union[Literal["channel"], str]
    message_id: Union[str, int]
    user_id: Union[str, int]
    message: CQHTTPMessage
    raw_message: Optional[str]
    font: Optional[int]
    sender: Sender
    guild_id: Optional[str]
    channel_id: Optional[str]

    def __repr__(self) -> str:
        return f'Event<{self.type}>: "{self.message}"'

    def get_plain_text(self) -> str:
        """获取消息的纯文本内容。

        Returns:
            消息的纯文本内容。
        """
        return self.message.get_plain_text()

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        """回复消息。

        Args:
            msg: 回复消息的内容，同 `call_api()` 方法。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError


class MessageSentEvent(CQHTTPEvent):
    """自身消息事件"""

    __event__ = "message_sent"
    post_type: Literal["message_sent"]
    message_type: Literal["private", "group"]
    sub_type: str
    message_id: int
    user_id: int
    message: CQHTTPMessage
    raw_message: str
    font: int
    sender: Sender

    def __repr__(self) -> str:
        return f'Event<{self.type}>: "{self.message}"'

    def get_plain_text(self) -> str:
        """获取消息的纯文本内容。

        Returns:
            消息的纯文本内容。
        """
        return self.message.get_plain_text()

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        """回复消息。

        Args:
            msg: 回复消息的内容，同 `call_api()` 方法。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError


class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    __event__ = "message.private"
    message_type: Literal["private"]
    sub_type: Literal["friend", "group", "group_self", "other"]

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        return await self.adapter.send_private_msg(
            user_id=self.user_id, message=CQHTTPMessage(msg)
        )


class PrivateMessageSentEvent(MessageSentEvent):
    """自身私聊消息"""

    __event__ = "message_sent.private"
    message_type: Literal["private", "group"]
    sub_type: Literal["friend", "group", "group_self", "other"]

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        return await self.adapter.send_private_msg(
            user_id=self.user_id, message=CQHTTPMessage(msg)
        )


class GroupMessageEvent(MessageEvent):
    """群消息"""

    __event__ = "message.group"
    message_type: Literal["group"]
    sub_type: Literal["normal", "anonymous", "notice"]
    group_id: int
    anonymous: Optional[Anonymous] = None

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        return await self.adapter.send_group_msg(
            group_id=self.group_id, message=CQHTTPMessage(msg)
        )


class GroupMessageSentEvent(MessageSentEvent):
    """自身群消息"""

    __event__ = "message_sent.group"
    message_type: Literal["group"]
    sub_type: Literal["normal", "anonymous", "notice"]
    group_id: int
    anonymous: Optional[Anonymous] = None

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        return await self.adapter.send_group_msg(
            group_id=self.group_id, message=CQHTTPMessage(msg)
        )


class NoticeEvent(CQHTTPEvent):
    """通知事件"""

    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str


class GroupUploadNoticeEvent(NoticeEvent):
    """群文件上传"""

    __event__ = "notice.group_upload"
    notice_type: Literal["group_upload"]
    user_id: int
    group_id: int
    file: File


class GroupAdminNoticeEvent(NoticeEvent):
    """群管理员变动"""

    __event__ = "notice.group_admin"
    notice_type: Literal["group_admin"]
    sub_type: Literal["set", "unset"]
    user_id: int
    group_id: int


class GroupDecreaseNoticeEvent(NoticeEvent):
    """群成员减少"""

    __event__ = "notice.group_decrease"
    notice_type: Literal["group_decrease"]
    sub_type: Literal["leave", "kick", "kick_me"]
    group_id: int
    operator_id: int
    user_id: int


class GroupIncreaseNoticeEvent(NoticeEvent):
    """群成员增加"""

    __event__ = "notice.group_increase"
    notice_type: Literal["group_increase"]
    sub_type: Literal["approve", "invite"]
    group_id: int
    operator_id: int
    user_id: int


class GroupBanNoticeEvent(NoticeEvent):
    """群禁言"""

    __event__ = "notice.group_ban"
    notice_type: Literal["group_ban"]
    sub_type: Literal["ban", "lift_ban"]
    group_id: int
    operator_id: int
    user_id: int
    duration: int


class FriendAddNoticeEvent(NoticeEvent):
    """好友添加"""

    __event__ = "notice.friend_add"
    notice_type: Literal["friend_add"]
    user_id: int


class GroupRecallNoticeEvent(NoticeEvent):
    """群消息撤回"""

    __event__ = "notice.group_recall"
    notice_type: Literal["group_recall"]
    group_id: int
    operator_id: int
    user_id: int
    message_id: int


class FriendRecallNoticeEvent(NoticeEvent):
    """好友消息撤回"""

    __event__ = "notice.friend_recall"
    notice_type: Literal["friend_recall"]
    user_id: int
    message_id: int


class NotifyEvent(NoticeEvent):
    """提醒事件"""

    __event__ = "notice.notify"
    notice_type: Literal["notify"]
    sub_type: str
    group_id: int
    user_id: int


class PokeNotifyEvent(NotifyEvent):
    """戳一戳"""

    __event__ = "notice.notify.poke"
    sub_type: Literal["poke"]
    target_id: int
    group_id: Optional[int] = None


class GroupLuckyKingNotifyEvent(NotifyEvent):
    """群红包运气王"""

    __event__ = "notice.notify.lucky_king"
    sub_type: Literal["lucky_king"]
    target_id: int


class GroupHonorNotifyEvent(NotifyEvent):
    """群成员荣誉变更"""

    __event__ = "notice.notify.honor"
    sub_type: Literal["honor"]
    honor_type: Literal["talkative", "performer", "emotion"]


class GroupTitleNotifyEvent(NotifyEvent):
    """群成员头衔变更"""

    __event__ = "notice.notify.title"
    sub_type: Literal["title"]
    group_id: int
    user_id: int
    title: str


class GroupCardNotifyEvent(NoticeEvent):
    """群成员名片更新"""

    __event__ = "notice.group_card"
    notice_type: Literal["group_card"]
    group_id: int
    user_id: int
    card_new: str
    card_old: str


class ReceiveOfflineFileEvent(NoticeEvent):
    """接收到离线文件"""

    __event__ = "notice.offline_file"
    notice_type: Literal["offline_file"]
    user_id: int
    file: OfflineFile


class OtherClientStatusEvent(NoticeEvent):
    """其他客户端在线状态变更"""

    __event__ = "notice.client_status"
    notice_type: Literal["client_status"]
    client: Device
    online: bool


class EssenceEvent(NoticeEvent):
    """精华消息变更"""

    __event__ = "notice.essence"
    notice_type: Literal["essence"]
    sub_type: Literal["add", "delete"]
    group_id: int
    sender_id: int
    operator_id: int
    message_id: int


class RequestEvent(CQHTTPEvent):
    """请求事件"""

    __event__ = "request"
    post_type: Literal["request"]
    request_type: str

    async def approve(self) -> Dict[str, Any]:
        """同意请求。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError

    async def refuse(self) -> Dict[str, Any]:
        """拒绝请求。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError


class FriendRequestEvent(RequestEvent):
    """加好友请求"""

    __event__ = "request.friend"
    request_type: Literal["friend"]
    user_id: int
    comment: str
    flag: str

    async def approve(self, remark: str = "") -> Dict[str, Any]:
        """同意请求。

        Args:
            remark: 好友备注。

        Returns:
            API 请求响应。
        """
        return await self.adapter.set_friend_add_request(
            flag=self.flag, approve=True, remark=remark
        )

    async def refuse(self) -> Dict[str, Any]:
        return await self.adapter.set_friend_add_request(flag=self.flag, approve=False)


class GroupRequestEvent(RequestEvent):
    """加群请求／邀请"""

    __event__ = "request.group"
    request_type: Literal["group"]
    sub_type: Literal["add", "invite"]
    group_id: int
    user_id: int
    comment: str
    flag: str

    async def approve(self) -> Dict[str, Any]:
        return await self.adapter.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=True
        )

    async def refuse(self, reason: str = "") -> Dict[str, Any]:
        """拒绝请求。

        Args:
            reason: 拒绝原因。

        Returns:
            API 请求响应。
        """
        return await self.adapter.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=False, reason=reason
        )


class MetaEvent(CQHTTPEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str


class LifecycleMetaEvent(MetaEvent):
    """生命周期"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: Literal["enable", "disable", "connect"]


class HeartbeatMetaEvent(MetaEvent):
    """心跳包"""

    __event__ = "meta_event.heartbeat"
    meta_event_type: Literal["heartbeat"]
    status: Status
    interval: int


class GuildMessageEvent(MessageEvent):
    """收到频道消息"""

    __event__ = "message.guild"
    message_type: Literal["guild"]
    sub_type: Literal["channel"]
    guild_id: str
    channel_id: str
    user_id: str
    message_id: str
    sender: Sender
    message: CQHTTPMessage

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        return await self.adapter.send_guild_channel_msg(
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            message=CQHTTPMessage(msg),
        )


class GuildMessageReactionUpdated(NoticeEvent):
    """频道消息表情贴更新"""

    __event__ = "notice.message_reactions_updated"
    notice_type: Literal["message_reactions_updated"]
    guild_id: str
    channel_id: str
    user_id: str
    message_id: str
    # current_reactions: ReactionInfo


class GuildChannelUpdate(NoticeEvent):
    """子频道信息更新"""

    __event__ = "notice.channel_updated"
    notice_type: Literal["channel_updated"]
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    old_info: ChannelInfo
    new_info: ChannelInfo


class GuildChannelCreated(NoticeEvent):
    """子频道创建"""

    __event__ = "notice.channel_created"
    notice_type: Literal["channel_created"]
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    channel_info: ChannelInfo


class GuildChannelDestoryed(NoticeEvent):
    """子频道删除"""

    __event__ = "notice.channel_destroyed"
    notice_type: Literal["channel_destroyed"]
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    channel_info: ChannelInfo


_cqhttp_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, CQHTTPEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_CQHTTPEvent]:
    """根据接收到的消息类型返回对应的事件类。

    Args:
        post_type: 请求类型。
        event_type: 事件类型。
        sub_type: 子类型。

    Returns:
        对应的事件类。
    """
    if sub_type is None:
        return _cqhttp_events[".".join((post_type, event_type))]
    return (
        _cqhttp_events.get(".".join((post_type, event_type, sub_type)))
        or _cqhttp_events[".".join((post_type, event_type))]
    )
