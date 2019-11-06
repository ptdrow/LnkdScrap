#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 18:53:04 2019

@author: ptdrow
"""
import sqlite3
import csv
from selenium import webdriver
import random
import time
import os

def open_browser(firefox_profile_path):
    profile = webdriver.FirefoxProfile(firefox_profile_path)
    return webdriver.Firefox(firefox_profile=profile)


def scroll_down_search_page(driver):
    height = driver.execute_script("return document.documentElement.scrollHeight")
    
    for i in range(2):
        driver.execute_script("window.scrollTo(0, "+ str(height//3*(i+1)) + ");")
    
        # Wait to load page
        SCROLL_PAUSE_TIME = random.randint(2,3)
        time.sleep(SCROLL_PAUSE_TIME)
    
        
def scroll_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    i=0
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        i+=1
        print(f"Scrolled times: {i}")
    
        # Wait to load page
        SCROLL_PAUSE_TIME = random.randint(1,2)
        time.sleep(SCROLL_PAUSE_TIME)
    
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_my_contacts(driver):
    driver.get('https://www.linkedin.com/mynetwork/invite-connect/connections/')
    scroll_down(driver)
    lista = driver.find_elements_by_class_name("list-style-none")
    lista.reverse()
    
    contacts = []
    i = 0
    #first two lists aren't contacts
    for element in lista[2:]:
        i += 1
        link = element.find_element_by_tag_name("a").get_property("href")
        name = element.find_elements_by_tag_name("span")[2].text
        name = name.replace(",","")
        occupation = element.find_elements_by_tag_name("span")[4].text
        occupation = occupation.replace(",",";")
        print(str(i) + ":" + name)
        contacts.append({"id": i, "nombre":name, "ocupacion":occupation, "url":link})
    
    return contacts

    
def add_to_graph(reference_id, contacts):
    if not os.path.exists("contacts"):
        os.mkdir("contacts")
    
    if not os.path.exists("contacts/connections.csv"):
        archivo = open("contacts/connections.csv", "w", encoding="utf8")
        archivo.write("Source,Target\n")
    else:
        archivo = open("contacts/connections.csv", "a", encoding="utf8")
    
    for contact in contacts:
        archivo.write(f"{reference_id},{contact['id']}\n")
    
    archivo.close()


def is_contact_in_db():
    pass

def go_to_contacts_page(driver,url):
    driver.get(url)
    time.sleep(random.randint(3,10))
    element = driver.find_element_by_xpath('//a[contains(@data-control-name,"topcard_view_all_connections")]')
    element.click()
    time.sleep(random.randint(10,15))
    

def get_this_page_contacts(driver, i):
    contacts = []
    scroll_down_search_page(driver)
    lista = driver.find_elements_by_class_name("search-result__wrapper")
    for element in lista:
        i += 1
        link = element.find_element_by_tag_name("a").get_property("href")
        name = element.find_elements_by_tag_name("span")[1].text.split("\n")[0]
        name = name.replace(",","")
        occupation = element.find_elements_by_tag_name("span")[7].text
        occupation = occupation.replace(",",";")
        print(f"{i:06d},{name},{occupation},{link}\n")
        contacts.append({"id": i, "nombre":name, "ocupacion":occupation, "url":link})
    return contacts, i
    
    
def get_other_contacts(driver,urls, ids):
    for id_, url in zip(ids,urls):
        go_to_contacts_page(driver,url)
                
        contacts = []
        i=0
        while True:
            page_contacts, i = get_this_page_contacts(driver,i)
            contacts.extend(page_contacts)
            
            if not click_siguiente(driver):
                break
        
        save_contacts(contacts, file="contacts/contacts" + str(id_) + ".csv", myself=None)
        
        
def save_contacts(contacts, file="contacts/contacts.csv", myself=None):
    archivo_salida = open(file, "w", encoding="utf8")
    #Get the data from all the elements of the list except the last two (after the reverse are the first two)
    archivo_salida.write(f"id,nombre,ocupacion,url\n")
    
    if myself:
        archivo_salida.write(f"0,{myself[0]},{myself[1]},{myself[2]}\n")
    
    for contact in contacts:
        i = contact['id']
        link = contact['url']
        name = contact['nombre']
        occupation = contact['ocupacion']
        archivo_salida.write(f"{i},{name},{occupation},{link}\n")
    
    archivo_salida.close()
    

#Conectar base de datos
def conectar_sql(filename="linkedin.db"):
    return sqlite3.connect(filename)


def verificar_tabla(connection, nombre_tabla):
    cursor = connection.cursor()
    cursor.execute('''SELECT name 
                   FROM sqlite_master 
                   WHERE type="table" AND name=?;''', nombre_tabla)
    connection.commit()
    if cursor.fetchone():
        exists = True
    else:
        exists = False
    
    return exists
        

def crear_tabla(connection):
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE contacts(
            [id] INTEGER PRIMARY KEY,
            [nombre] TEXT, 
            [ocupacion] TEXT, 
            [url] TEXT, 
            [para_revisar] INTEGER,
            [revisado] BOOLEAN, 
            [fecha_revisado] TIMESTAMP, 
            [shortest_distance] INTEGER)''')
    connection.commit()


def insertar_contacto(connection, contact):
    sql = '''INSERT INTO contacts(nombre, ocupacion, url) VALUES(?,?,?)'''
    nombre = contact[1]
    ocupacion = contact[2]
    url = contact[3]
    datos = (nombre,ocupacion, url)
    cursor = connection.cursor()
    cursor.execute(sql,datos)
    connection.commit()


def encuesta_contactos(connection):
    sql = 'SELECT id, nombre from contacts'
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    rows = cursor.fetchall()
    respuestas = []
    for row in rows:
        respuesta = input("Del 1 al 5, que tanto quieres revisar el perfil de " + row[1] + ":")
        respuestas.append((row[0],respuesta))
    
    return respuestas


def update_para_revisar(connection, contact_id, value):
    sql = ''' UPDATE contacts
              SET para_revisar = ? 
              WHERE id = ?'''
    datos = (value,contact_id)
    cursor = connection.cursor()
    cursor.execute(sql, datos)
    connection.commit()
    

def select_contactos(connection, cantidad):
    cursor = connection.cursor()
    sql = '''SELECT id, para_revisar 
             FROM contacts 
             ORDER BY para_revisar DESC;'''
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    ids = []
    for row in rows[:cantidad]:
        ids.append(row[0])
    return ids


def ids_to_string(ids):
    s = ""
    for id_ in ids:
        s = s + "," + str(id_)
    return s[1:]


def get_urls(connection,ids):
    string_ids = ids_to_string(ids)
    sql = 'SELECT url FROM contacts WHERE id IN (' + string_ids + ');'
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    urls = []
    for row in rows:
        urls.append(row[0])
    
    return urls
    

def update_distance(connection,contact_id, distance):
    sql = ''' UPDATE contacts
              SET shortest_distance = ? 
              WHERE id = ?'''
    datos = (distance,contact_id)
    cursor = connection.cursor()
    cursor.execute(sql, datos)
    connection.commit()

        
def click_siguiente(driver):
    element = driver.find_element_by_xpath('//button[contains(@aria-label,"Siguiente")]')
    if element.is_enabled():
        element.click()
        time.sleep(random.randint(10,15))
        return(True)
    else:
        return(False)


if __name__ == "__main__":
    import my_credentials
    
    driver = open_browser(my_credentials.firefox_profile_path)
    contactos = get_my_contacts(driver)
    save_contacts(contactos, 
                  myself = my_credentials.myself)
    
    add_to_graph("0", contactos)
    
    conn = conectar_sql()
    
    if not verificar_tabla(conn, ["contacts"]):
        crear_tabla(conn)
        archivo = open("contacts/contacts.csv", "r", encoding="utf8")
        lectura = csv.reader(archivo, delimiter=',')
        next(lectura)
        for contacto in lectura:
            insertar_contacto(conn, contacto)
    
#    respuestas = encuesta_contactos(conn)
#    
#    for contact_id, respuesta in respuestas:
#        update_para_revisar(conn, contact_id, respuesta)
    
    contact_ids = select_contactos(conn, 10)
    urls = get_urls(conn, contact_ids)
    
    get_other_contacts(driver,urls, contact_ids)
    
    driver.quit()
    conn.close()
        
    
    driver.find