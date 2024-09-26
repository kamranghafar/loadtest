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

        # Initialize browser settings
        self.driver = self.initialize_browser()

        # Open the login page and perform initial actions
        self.initial_actions()

    def initialize_browser(self):
        """Initializes the Selenium WebDriver."""
        browser = "chrome"
        headless = True  # Replace with configuration system's headless selection logic

        try:
            if browser == "chrome":
                options = ChromeOptions()
                service = ChromeService(executable_path=configuration_system.driver_location)

                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1200,1200")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-web-security")
                if headless:
                    options.add_argument("--headless")

                driver = webdriver.Chrome(service=service, options=options)
                self.logger.info(f"{browser.capitalize()} browser started successfully.")
                return driver
            else:
                raise ValueError(f"Unsupported browser: {browser}")

        except (WebDriverException, ValueError) as e:
            self.logger.error(f"Error setting up the browser: {e}")
            raise

    def initial_actions(self):
        """Opens the login page and performs necessary actions."""
        try:
            self.driver.get("https://testwindow.beelinks.solutions/")
            self.logger.info(f"Opened URL: {self.driver.current_url}")

            # Wait for the body to load to ensure the page is fully loaded
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            self.start_form_fill_and_chat_interaction()

        except TimeoutException as e:
            self.logger.error(f"TimeoutException during initial actions: {e}")
            self.cleanup()
            raise

    def start_form_fill_and_chat_interaction(self):
        """Handles form filling and chat interaction."""
        self.logger.info("Starting form fill and chat test...")
        time.sleep(30)  # Consider replacing with WebDriverWait if possible
        self.driver.switch_to.frame(0)
        self.wait_for_element(By.ID, "title", 40).click()
        time.sleep(5)
        self.driver.switch_to.default_content()
        time.sleep(2)
        self.driver.switch_to.frame(1)
        self.wait_for_element(By.ID, "btnChat", 30).click()
        time.sleep(2)

        # Fill chat form
        self.fill_chat_form()

    def wait_for_element(self, by, value, timeout):
        """Waits for an element to be present."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def fill_chat_form(self):
        """Fills in the chat form fields."""
        try:
            self.driver.find_element(By.ID, "field3").send_keys("test")
            self.driver.find_element(By.ID, "field4").send_keys("test@test.com")
            self.driver.find_element(By.ID, "field5").send_keys("12212122121212")
            time.sleep(2)  # Consider reducing sleep or replacing with appropriate waits
            self.driver.find_element(By.ID, "btnStartChat").click()
            time.sleep(5)
            self.driver.find_element(By.ID, "chatMessage")  # Just ensure this is loaded

        except TimeoutException as e:
            self.logger.error(f"TimeoutException during form fill: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """Cleans up the WebDriver instance."""
        if hasattr(self, 'driver'):
            self.driver.quit()

    @task
    def chattest(self):
        """Tests the chat functionality."""
        start_time = time.time()  # Start the timer here for accurate response time measurement

        try:
            chat_input = self.driver.find_element(By.ID, "chatMessage")
            chat_input.send_keys("test message")
            chat_input.send_keys(Keys.RETURN)

            # Measure response time
            response_time = (time.time() - start_time) * 1000
            self.log_request("Chat initiated successfully.", response_time)

        except TimeoutException as e:
            self.log_request("TimeoutException occurred during chat initiation.", None, str(e))
        except Exception as e:
            self.log_request("An error occurred during chat initiation.", None, str(e))

    def log_request(self, message, response_time, exception=None):
        """Logs the request and fires Locust events."""
        if response_time is not None:
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Chat initiated",
                response_time=response_time,
                response_length=0,
                exception=None
            )
            self.logger.info(message)
        else:
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Chat initiated",
                response_time=None,
                response_length=0,
                exception=exception
            )
            self.logger.error(message)
