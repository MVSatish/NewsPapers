import scrapy,wget,json
from scrapy.http import FormRequest
from scrapy.http import Request
from epapers.items import EpapersItem
from epapers.settings import mypath
import time
from datetime import datetime
import subprocess,os,uuid 
class IESpider(scrapy.Spider):
    name = "iexpress"
    allowed_domains = ["newindianexpress.com"]
    start_urls =["http://epaper.newindianexpress.com"]
    date_today = time.strftime('%Y-%m-%d')
    #For finding password for the PDF Page
    def find_hyphen(self, s):
        try:
            start = 0
            end = s.index( "-", start )
            return s[0:end+2]
        except ValueError:
            return ""
    
    def parse(self, response):
    	# Mumbai Volume number, replace 226 for Delhi, check IE portal for other deisred editions
    	get_volume = str(236)
    	yield Request("http://epaper.newindianexpress.com/api/volumedates_v3/"+get_volume, callback=self.parse_for_volumes)
    def parse_for_item(self,response):
		# Parse for item downloads the PDF files and stores in "iexpress" dated folder in the epapers directory
		volume_code = response.meta['volume_code']
		total_pages_meta = json.loads(response.body_as_unicode())
		volume_pages ={}
		for one_page in total_pages_meta:
			volume_pages[total_pages_meta[one_page]['pagenum']] = total_pages_meta[one_page]['key']
		for pagenumber, codeword in volume_pages.iteritems():
			password = self.find_hyphen(codeword)
			onelink = "http://cache.epapr.in/"+volume_code+"/"+codeword+"-combined.pdf"
			unique_file_name = str(uuid.uuid4())
			filename = unique_file_name+".pdf"
			decrypted_filename = unique_file_name+"-decrypted.pdf"
			wget.download(onelink,filename)
			command = "qpdf --password="+password+" --decrypt "+filename+" "+decrypted_filename
			subprocess.call([command], shell=True)
			os.remove(filename)
			if not os.path.exists(mypath+"/iexpress"):
				os.makedirs(mypath+"/iexpress")
			if not os.path.exists(mypath+"/iexpress/"+self.date_today):
				os.makedirs(mypath+"/iexpress/"+self.date_today)
			os.rename(decrypted_filename, mypath+"/iexpress/"+self.date_today+"/"+decrypted_filename)
		yield None
    def parse_for_volumes(self,response):
    	jsonresponse = json.loads(response.body_as_unicode())
    	for date, vcode in jsonresponse.iteritems():
		d = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
		edition_date = d.strftime("%Y-%m-%d")
		if edition_date == self.date_today:
			vcode = str(vcode)
			metaurl = "http://epaper.newindianexpress.com/pagemeta/get/"+vcode
			yield Request(metaurl, callback = self.parse_for_item, meta ={"volume_code": vcode})
		else:
			yield None