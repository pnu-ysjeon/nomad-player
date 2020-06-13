from abc import ABCMeta, abstractmethod
from multiprocessing import Pool
from module.utils import shutdown, get_driver, bugs_login
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Migrator(metaclass=ABCMeta):
    def __init__(self, email, pw):
        self.email = email
        self.pw = pw
        self.failure_list = []

    @abstractmethod
    def login(self, driver):
        pass

    @abstractmethod
    def add_playlist(self, plist):
        pass

    def read_playlist(self):
        try:
            with open('Playlist.txt', 'r', encoding="utf-8") as f:
                plist = f.readlines()
                f.close()
                return plist
        except FileNotFoundError:
            shutdown(msg='Failed to load local playlist')

    def save_failure(self, plist=None):
        with open('Failure_list.txt', 'a', encoding="utf-8") as f:
            if plist is not None:
                for song in plist:
                    f.write("%s" % song)
            for song in self.failure_list:
                f.write("%s" % song)

    def migrate(self):
        # add playlist with multiprocessing
        process_num = 4
        plist = self.read_playlist()
        n = int(len(plist) / process_num + len(plist) % process_num)
        plist = [plist[i:i + n] for i in range(0, len(plist), n)]

        pool = Pool(processes=process_num)
        pool.map(self.add_playlist, plist)
        shutdown(msg='Migration Successed!')


class BugsMigrator(Migrator):
    def login(self, driver):
        return bugs_login(driver=driver, email=self.email, pw=self.pw)

    def add_playlist(self, plist):
        driver = get_driver()
        success = self.login(driver)
        WebDriverWait(driver, 3) \
            .until(EC.presence_of_element_located((By.ID, 'headerSearchInput')))

        if success:
            for song in plist:
                # search song info
                driver.find_element_by_id('headerSearchInput').clear()
                driver.find_element_by_id('headerSearchInput').send_keys(song)
                driver.find_element_by_id('hederSearchFormButton').click()

                try:
                    driver.find_element_by_id('DEFAULT0')
                    # add song to first playlist
                    driver.find_element_by_xpath('//*[@id="DEFAULT0"]/table/tbody/tr[1]/td[8]/a').click()
                    driver.find_element_by_xpath('//*[@id="track2playlistScrollArea"]/div/div/ul/li[2]/a').click()
                    driver.find_element_by_xpath('//*[@id="bugsAlert"]/section/p/button').click()
                except NoSuchElementException:
                    # add failure playlist
                    self.failure_list.append(song)
                    pass

        self.save_failure(plist=None if success else plist)
        print('Add Playlist to Bugs Successed')