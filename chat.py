import pandas as pd
from locust import HttpUser, task, between
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import urllib3
import time
import logging
from configuration import configuration_system

# Suppress SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BeelinksUser(HttpUser):
    wait_time = between(5, 10)

    def on_start(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Select browser and headless option
        browser = "chrome"
        headless = False  # Replace with configuration system's headless selection logic

        try:
            if browser == "chrome":
                options = ChromeOptions()
                service = ChromeService(executable_path=configuration_system.driver_location)
            else:
                raise ValueError(f"Unsupported browser: {browser}")

            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1200,1200")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-web-security")
            if headless:
                options.add_argument("--headless")

            # Initialize WebDriver
            self.driver = webdriver.Chrome(service=service, options=options)
            self.logger.info(f"{browser.capitalize()} browser started successfully.")

        except (WebDriverException, ValueError) as e:
            self.logger.error(f"Error setting up the browser: {e}")
            raise

        try:
            # Open the login page
            self.driver.get("https://testwindow.beelinks.solutions/")
            self.logger.info(f"Opened URL: {self.driver.current_url}")

            # Wait for the body to load to ensure the page is fully loaded
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Start form filling and chat interaction
            self.logger.info("Starting form fill and chat test...")
            time.sleep(30)
            self.driver.switch_to.frame(0)
            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.ID, "title"))
            ).click()
            time.sleep(5)
            self.driver.switch_to.default_content()
            time.sleep(2)
            self.driver.switch_to.frame(1)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "btnChat"))
            ).click()
            time.sleep(2)

            time.sleep(3)
            self.driver.find_element(By.ID, "field3").send_keys("test")
            self.driver.find_element(By.ID, "field4").send_keys("test@test.com")
            self.driver.find_element(By.ID, "field5").send_keys("12212122121212")
            time.sleep(2)

            self.driver.find_element(By.ID, "btnStartChat").click()
            time.sleep(5)
            chat_input = self.driver.find_element(By.ID, "chatMessage")

        except TimeoutException as e:
            self.logger.error(f"TimeoutException during login: {e}")
            self.driver.quit()
            raise

    @task
    def chattest(self):
        start_time = time.time()  # Start the timer here for accurate response time measurement

        try:
            chat_input = self.driver.find_element(By.ID, "chatMessage")
            chat_input.send_keys("test message")
            chat_input.send_keys(Keys.RETURN)
            #
            # wait = WebDriverWait(self.driver, 15)
            # status_elements = wait.until(
            #     EC.presence_of_all_elements_located((By.XPATH, '//span[@class="msg-status ng-star-inserted"]'))
            # )
            #
            # if status_elements:
            #     latest_status = status_elements[-1].text.strip().lower()
            #     assert latest_status in ["sent", "accepted", "delivered", "seen"], f"Unexpected status: {latest_status}"
            # else:
            #     assert False, "Status elements not found or empty"
            #
            # time.sleep(10)

            # Measure response time
            # time.sleep(5)
            # self.driver.refresh()
            response_time = (time.time() - start_time) * 1000

            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Login and Navigate to Tickets",
                response_time=response_time,
                response_length=0,
                exception=None
            )
            self.logger.info("Chat initiated successfully.")

        except TimeoutException as e:
            self.logger.error(f"TimeoutException occurred: {e}")
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Chat initiated",
                response_time=None,
                response_length=0,
                exception=str(e)
            )
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Chat initiated",
                response_time=None,
                response_length=0,
                exception=str(e)
            )
