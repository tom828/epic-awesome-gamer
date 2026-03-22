# -*- coding: utf-8 -*-
"""
@Time    : 2025/7/16 22:13
@Author  : QIN2DIM
@GitHub  : https://github.com/QIN2DIM
@Desc    :
"""
import asyncio
import json
import time
from contextlib import suppress

from hcaptcha_challenger.agent import AgentV
from loguru import logger
from playwright.async_api import expect, Page, Response

from settings import settings

URL_CLAIM = "https://store.epicgames.com/en-US/free-games"


class LoginFailedException(Exception):
    """登录失败异常"""
    pass


class EpicAuthorization:

    def __init__(self, page: Page):
        self.page = page

        self._is_login_success_signal = asyncio.Queue()
        self._is_refresh_csrf_signal = asyncio.Queue()
        self._login_error_code = None  # 存储登录错误码

    async def _on_response_anything(self, r: Response):
        if r.request.method != "POST" or "talon" in r.url:
            return

        with suppress(Exception):
            result = await r.json()

            # 记录所有 POST 响应的 URL，便于调试
            logger.debug(f"📡 API 响应: {r.url} | 状态码: {r.status}")

            if "/id/api/login" in r.url:
                # 记录完整的登录 API 响应
                logger.debug(f"🔍 登录 API 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                if result.get("errorCode"):
                    # 记录错误码并通知登录失败
                    self._login_error_code = result.get("errorCode")
                    error_msg = result.get("errorMessage", "未知错误")
                    # 记录完整的错误信息
                    logger.error(f"❌ 登录失败: errorCode={self._login_error_code}, message={error_msg}")
                    logger.error(f"❌ 完整错误响应: {json.dumps(result, ensure_ascii=False)}")
                    # 放入失败信号，中断等待
                    self._is_login_success_signal.put_nowait({"error": True, "code": self._login_error_code, "full_response": result})
                else:
                    # 登录成功，记录 accountId
                    if result.get("accountId"):
                        logger.success(f"✅ 登录 API 返回成功: accountId={result.get('accountId')}")
            elif "/id/api/analytics" in r.url and result.get("accountId"):
                self._is_login_success_signal.put_nowait(result)
            elif "/account/v2/refresh-csrf" in r.url and result.get("success", False) is True:
                self._is_refresh_csrf_signal.put_nowait(result)

    async def _handle_right_account_validation(self):
        """
        以下验证仅会在登录成功后出现
        Returns:

        """
        await self.page.goto("https://www.epicgames.com/account/personal", wait_until="networkidle")

        btn_ids = ["#link-success", "#login-reminder-prompt-setup-tfa-skip", "#yes"]

        # == 账号长期不登录需要做的额外验证 == #

        while self._is_refresh_csrf_signal.empty() and btn_ids:
            await self.page.wait_for_timeout(500)
            action_chains = btn_ids.copy()
            for action in action_chains:
                with suppress(Exception):
                    reminder_btn = self.page.locator(action)
                    await expect(reminder_btn).to_be_visible(timeout=1000)
                    await reminder_btn.click(timeout=1000)
                    btn_ids.remove(action)

    async def _login(self) -> bool | None:
        # 重置错误码
        self._login_error_code = None

        # 尽可能早地初始化机器人
        agent = AgentV(page=self.page, agent_config=settings)

        # {{< SIGN IN PAGE >}}
        logger.debug("Login with Email")

        try:
            point_url = "https://www.epicgames.com/account/personal?lang=en-US&productName=egs&sessionInvalidated=true"
            await self.page.goto(point_url, wait_until="domcontentloaded")

            # 1. 使用电子邮件地址登录
            email_input = self.page.locator("#email")
            await email_input.clear()
            await email_input.type(settings.EPIC_EMAIL)

            # 2. 点击继续按钮
            await self.page.click("#continue")

            # 3. 输入密码
            password_input = self.page.locator("#password")
            await password_input.clear()
            await password_input.type(settings.EPIC_PASSWORD.get_secret_value())

            # 4. 点击登录按钮
            await self.page.click("#sign-in")

            # 并行启动：验证码处理 + 登录结果等待
            # 关键改进：使用 wait_for 快速检测密码错误
            async def wait_for_login_result():
                """等待登录结果（成功或失败）"""
                return await self._is_login_success_signal.get()

            async def handle_captcha():
                """处理验证码（如果需要）"""
                try:
                    await agent.wait_for_challenge()
                except Exception:
                    pass  # 验证码处理失败不影响登录结果判断

            # 同时启动两个任务
            captcha_task = asyncio.create_task(handle_captcha())
            result_task = asyncio.create_task(wait_for_login_result())

            # 第一阶段：15秒内快速检测密码错误
            try:
                done, pending = await asyncio.wait(
                    [result_task],
                    timeout=15,
                    return_when=asyncio.FIRST_COMPLETED
                )

                if result_task in done:
                    result = result_task.result()
                    # 检查是否是登录失败信号
                    if result.get("error"):
                        captcha_task.cancel()
                        error_code = result.get("code", "")
                        if "invalid_account_credentials" in error_code:
                            logger.error("❌ 账号或密码错误")
                        elif "account_locked" in error_code:
                            logger.error("❌ 账号已被锁定")
                        else:
                            logger.error(f"❌ 登录失败: {error_code}")
                        return None

                    # 登录成功（无验证码或已通过）
                    if result.get("accountId"):
                        captcha_task.cancel()
                        logger.success("✅ 登录成功")
                        await asyncio.wait_for(self._handle_right_account_validation(), timeout=60)
                        logger.success("✅ 账号验证成功")
                        return True
            except asyncio.CancelledError:
                pass

            # 第二阶段：继续等待验证码处理后的结果（最多再等 60 秒）
            try:
                result = await asyncio.wait_for(self._is_login_success_signal.get(), timeout=60)

                if result.get("error"):
                    error_code = result.get("code", "")
                    if "invalid_account_credentials" in error_code:
                        logger.error("❌ 账号或密码错误")
                    elif "account_locked" in error_code:
                        logger.error("❌ 账号已被锁定")
                    else:
                        logger.error(f"❌ 登录失败: {error_code}")
                    return None

                logger.success("✅ 登录成功")
                await asyncio.wait_for(self._handle_right_account_validation(), timeout=60)
                logger.success("✅ 账号验证成功")
                return True

            except asyncio.TimeoutError:
                logger.error("❌ 登录超时")
                return None

        except asyncio.TimeoutError:
            logger.error("❌ 登录超时，请检查账号密码")
            return None
        except Exception as err:
            logger.warning(f"登录异常: {err}")
            return None
        finally:
            # 确保清理任务
            try:
                captcha_task.cancel()
            except:
                pass

    async def invoke(self):
        self.page.on("response", self._on_response_anything)

        for _ in range(3):
            await self.page.goto(URL_CLAIM, wait_until="domcontentloaded")

            if "true" == await self.page.locator("//egs-navigation").get_attribute("isloggedin"):
                logger.success("✅ Epic Games 已登录")
                return True

            if await self._login():
                return
