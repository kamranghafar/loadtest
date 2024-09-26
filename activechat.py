import pandas as pd
from locust import HttpUser, task, between
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import urllib3
import time
import logging
import random

from configuration import configuration_system

# Suppress SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BeelinksUser(HttpUser):
    wait_time = between(5, 10)

    used_users = set()  # Static variable to store used users

    @staticmethod
    def load_users_from_excel(file_path):
        try:
            df = pd.read_excel(file_path)
            users = df.to_dict('records')  # Convert each row to a dictionary
            return users
        except Exception as e:
            logging.error(f"Error loading users from Excel: {e}")
            return []

    def get_unique_user(self):
        # Load users from Excel and filter out used ones
        users = self.load_users_from_excel(configuration_system.excel_file)
        available_users = [user for user in users if user['email'] not in self.used_users]

        if not available_users:
            self.logger.error("No more unique users available.")
            raise ValueError("All users have been used.")

        # Select a random user from the available ones
        selected_user = random.choice(available_users)
        self.used_users.add(selected_user['email'])  # Mark the user as used
        return selected_user

    def on_start(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Select browser and headless option
        browser = "chrome"  # Assuming you're using Chrome here, adjust as necessary
        headless = True  # Replace with configuration system's headless selection logic

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

            # Initialize WebDriver using the standalone ChromeDriver
            self.driver = webdriver.Chrome(service=service, options=options)
            self.logger.info(f"{browser.capitalize()} browser started successfully.")

        except (WebDriverException, ValueError) as e:
            self.logger.error(f"Error setting up the browser: {e}")
            raise

        # Get a unique user for this session
        self.user = self.get_unique_user()

        try:
            # Open the login page
            self.driver.get(configuration_system.loadtestURL)
            self.logger.info(f"Opened URL: {self.driver.current_url}")

            # Wait for the body to load to ensure the page is fully loaded
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Wait for the email input field and enter email
            self.logger.info("Waiting for email field...")
            email_field = WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(self.user["email"])

            # Wait for the password field and enter password
            self.logger.info("Waiting for password field...")
            password_field = WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys(self.user["password"])

            # Wait for the login button and click it
            self.logger.info("Waiting for login button...")
            login_button = WebDriverWait(self.driver, 120).until(
                EC.element_to_be_clickable((By.ID, "login-submit"))
            )
            login_button.click()

        except TimeoutException as e:
            self.logger.error(f"TimeoutException during login: {e}")
            self.driver.quit()
            raise
        except Exception as e:
            self.logger.error(f"An error occurred during login: {e}")
            self.driver.quit()
            raise

    @task
    def accept_chat(self):
        start_time = time.time()
        try:
            # Wait for the tickets link and click it
            self.logger.info("accepting chat...")

            # Try clicking the avatar (proceed if not found)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    "//div[contains(@class, 'avatar') and contains(@class, 'ava-xs') and contains(@class, 'b-2')]"))
                ).click()
                self.logger.info("Avatar found and clicked.")
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.warning(f"Avatar not found: {e}. Proceeding without clicking it.")

            # Try clicking the 'Not Accepting Chats' checkbox (proceed if not found)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[@title='Not Accepting Chats']//input[@type='checkbox']"))
                ).click()
                self.logger.info("Checkbox found and clicked.")
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.warning(f"Checkbox not found: {e}. Proceeding without clicking it.")

                # Try clicking the 'Tickets' checkbox (proceed if not found)
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//li[@id="nav-tickets"]/a'))
                    ).click()
                    self.logger.info("Ticket button found and clicked.")
                except (TimeoutException, NoSuchElementException) as e:
                    self.logger.warning(f"Ticket button not found: {e}. Proceeding without clicking it.")

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
            self.logger.info("Successfully activated chat.")

        except TimeoutException as e:
            self.logger.error(f"TimeoutException occurred: {e}")
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Login and Navigate to Tickets",
                response_time=None,
                response_length=0,
                exception=str(e)
            )
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            self.environment.events.request.fire(
                request_type="UI Interaction",
                name="Login and Navigate to Tickets",
                response_time=None,
                response_length=0,
                exception=str(e)
            )
