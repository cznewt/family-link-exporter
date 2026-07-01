"""Pydantic models for the (undocumented) Kids Management API responses.

The API returns camelCase JSON and adds/removes fields over time, so every model
ignores unknown fields and makes all but the essentials optional. The goal is to
degrade gracefully, not to validate Google's schema.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


# --------------------------------------------------------------------------- #
# /people/{id}/appsandusage
# --------------------------------------------------------------------------- #
class UsageLimit(_Base):
    daily_usage_limit_mins: int | None = Field(None, alias="dailyUsageLimitMins")
    enabled: bool = False


class AlwaysAllowedAppInfo(_Base):
    # Present and == "alwaysAllowedStateEnabled" when the app is always allowed.
    always_allowed_state: str | None = Field(None, alias="alwaysAllowedState")


class SupervisionSetting(_Base):
    hidden: bool = False  # "hidden" == blocked in Family Link terms
    usage_limit: UsageLimit | None = Field(None, alias="usageLimit")
    always_allowed_app_info: AlwaysAllowedAppInfo | None = Field(
        None, alias="alwaysAllowedAppInfo"
    )
    google_search_disabled: bool | None = Field(None, alias="googleSearchDisabled")
    hidden_state_locked: bool | None = Field(None, alias="hiddenStateLocked")

    @property
    def always_allowed(self) -> bool:
        info = self.always_allowed_app_info
        return bool(info and info.always_allowed_state == "alwaysAllowedStateEnabled")


class App(_Base):
    package_name: str = Field(alias="packageName")
    title: str = ""
    supervision_setting: SupervisionSetting = Field(
        default_factory=SupervisionSetting, alias="supervisionSetting"
    )
    install_time_millis: str | None = Field(None, alias="installTimeMillis")
    app_source: str | None = Field(None, alias="appSource")
    device_ids: list[str] = Field(default_factory=list, alias="deviceIds")


class AppId(_Base):
    android_app_package_name: str | None = Field(None, alias="androidAppPackageName")


class UsageDate(_Base):
    year: int = 0
    month: int = 0
    day: int = 0


class AppUsageSession(_Base):
    # `usage` is a duration string in seconds, e.g. "1809s" or "1809.5s".
    # Despite the name these are per-app, per-device, per-DAY rollups, not
    # discrete foreground/background events.
    usage: str = "0s"
    app_id: AppId = Field(default_factory=AppId, alias="appId")
    device_mud_id: str | None = Field(None, alias="deviceMudId")
    mode_type: str | None = Field(None, alias="modeType")
    date: UsageDate = Field(default_factory=UsageDate)

    def usage_seconds(self) -> float:
        try:
            return float(self.usage.rstrip("s"))
        except (ValueError, AttributeError):
            return 0.0


class DeviceDisplayInfo(_Base):
    model: str = ""
    friendly_name: str = Field("", alias="friendlyName")
    last_activity_time_millis: str | None = Field(None, alias="lastActivityTimeMillis")


class DeviceInfo(_Base):
    device_id: str = Field("", alias="deviceId")
    display_info: DeviceDisplayInfo = Field(
        default_factory=DeviceDisplayInfo, alias="displayInfo"
    )


class AppUsage(_Base):
    apps: list[App] = Field(default_factory=list)
    device_info: list[DeviceInfo] = Field(default_factory=list, alias="deviceInfo")
    app_usage_sessions: list[AppUsageSession] = Field(
        default_factory=list, alias="appUsageSessions"
    )
    last_activity_refresh_timestamp_millis: str | None = Field(
        None, alias="lastActivityRefreshTimestampMillis"
    )


# --------------------------------------------------------------------------- #
# /families/mine/members
# --------------------------------------------------------------------------- #
class Profile(_Base):
    display_name: str = Field("", alias="displayName")
    given_name: str = Field("", alias="givenName")
    email: str = ""


class MemberSupervisionInfo(_Base):
    is_supervised_member: bool = Field(False, alias="isSupervisedMember")


class Member(_Base):
    user_id: str = Field("", alias="userId")
    role: str = ""
    profile: Profile = Field(default_factory=Profile)
    member_supervision_info: MemberSupervisionInfo | None = Field(
        None, alias="memberSupervisionInfo"
    )

    @property
    def is_supervised(self) -> bool:
        info = self.member_supervision_info
        return bool(info and info.is_supervised_member)

    @property
    def label(self) -> str:
        return self.profile.given_name or self.profile.display_name or self.user_id


class MembersResponse(_Base):
    members: list[Member] = Field(default_factory=list)
    my_user_id: str = Field("", alias="myUserId")
