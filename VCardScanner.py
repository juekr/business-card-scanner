#!/usr/bin/env python
# coding: utf-8

from imutils.perspective import four_point_transform
import pytesseract
import imutils
import cv2
import re
from os.path import exists
from glob import glob
from skimage.exposure import is_low_contrast
from pprint import pprint
from operator import itemgetter

class VCardScanner:
	images: list[str] = []
	debug: bool = False
	low_contrast_threshold:float = 0.65
	resize_width:int = 800

	def __init__(self, img = None, debug = False)-> None:
		self.debug = debug
		if img is None:
			return
		if type(img) is str:
			img = [img]
		if type(img) is list:
			img = [elem for elem in img if exists(elem)]
			self.images = img

	def add_image_by_path(self, img)-> bool:
		if exists(img):
			self.images.append(img)
			return True
		return False
	
	def ocr_init(self, original_image):
		image = original_image.copy()
		width = original_image.shape[0]
		height = original_image.shape[1]
		new_width = self.resize_width
		new_height = self.resize_width * (width/height)
		dim = (int(new_width), int(new_height))
		dim += ((dim[0] / float(dim[1])), )

		return (cv2.resize(image, (dim[0], dim[1]), interpolation=cv2.INTER_AREA), dim)
		#return self.gray(image)
	
	def gray(self, image):
		return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	def blur(self, image):
		blurred = cv2.GaussianBlur(image,(5,5),0) 
		#edged = cv2.Canny(blurred, 30, 150)
		ret, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
		return thresh
	
	def contours(self, image):
		cnts = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
		# initialize a contour that corresponds to the business card outline
		cardCnt = None
		for c in cnts:
			# approximate the contour
			peri = cv2.arcLength(c, True)
			approx = cv2.approxPolyDP(c, 0.02 * peri, True)
			# if this is the first contour we've encountered that has four
			# vertices, then we can assume we've found the business card
			if len(approx) == 4:
				cardCnt = approx
				break
		# if the business card contour is empty then our script could not
		# find the  outline of the card, so raise an error
		if cardCnt is None:
			return None
		return cardCnt

	def debug_out(self, image, contours = None, message = ""):#
		if self.debug is False:
			return
		else:
			print(message)
			output = image.copy()
			if contours is not None:
				cv2.drawContours(output, [contours], -1, (0, 255, 0), 2)
			cv2.imshow(f"Debug: {message}", output)
			cv2.waitKey(0)


	def approach_approx(self, image_path, iterations):
		original_image = cv2.imread(image_path)
		image, dimensions = self.ocr_init(original_image)
		results = []

		for contrast in range(1, 150, int(150/iterations)):
			for fraction in range(1, 20, int(20/iterations)):
				fraction = fraction/10
				gray = self.gray(cv2.convertScaleAbs(image, alpha=fraction, beta=contrast) )
				thresh = self.blur(gray)
				cardCnt = self.contours(thresh)
				if cardCnt is None:
					continue

				# skips if self.debug is False
				self.debug_out(image=image, contours = cardCnt, message=f"contrast: {contrast}, fraction: {fraction}")

				# apply a four-point perspective transform to the *original* image to
				# obtain a top-down bird's-eye view of the business card
				card = four_point_transform(original_image, cardCnt.reshape(4, 2) * dimensions[2]) # dimensions[2] = ration
				# show transformed image

				# convert the business card from BGR to RGB channel ordering and then
				# OCR it
				rgb = cv2.cvtColor(card, cv2.COLOR_BGR2RGB)
				text = pytesseract.image_to_string(rgb, lang="deu")

				phoneNums = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
				emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text)
				nameExp = r"^[\w'\-,.][^0-9_!¡?÷?¿/\\+=@#$%ˆ&*(){}|~<>;:[\]]{2,}"
				names = re.findall(nameExp, text)
				addrExp = r"([\S ]*)[\s,|]*([\S ]+?)\s*(\d+\s*[a-zA-Z]*\s*([-\/]\s*\d*\s*\w?\s*)*)[\s,|]*(\d{5})[\s,|]*([\S ]+)"
				city = re.findall(addrExp, text)

				json = {
					"phone": [ num.strip().strip("(").strip(")").strip("-").strip(" ") for num in phoneNums ],
					"name": [ name.strip() for name in names],
					"email": [ email.strip() for email in emails ],
					"address": [ (", ".join(line)).strip() for line in city ],
					"alpha": fraction,
					"contrast": contrast
				}
				results.append(json)
		return self.max_quality_dataset(results)

	def scan_and_ocr(self):
		for i in self.images:
			pprint(self.approach_approx(i, 12))

	def scan_and_ocr_bak(self):
		results = []

		# load the input image from disk, resize it, and compute the ratio
		# of the *new* width to the *old* width
		#scale_percent = 100 # percent of original size

		for i in self.images:
			result = self.approach_approx(i)
			contrast = 0
			while contrast < 150:
				contrast = contrast + 5
				fraction = 0.0
				while fraction < 2:
					fraction = fraction + .1
					orig = cv2.imread(i)
					image = orig.copy()
					# image = imutils.resize(image, width=600)

					width = orig.shape[0]
					height = orig.shape[1]
					new_width = self.resize_width
					new_height = self.resize_width * (width/height)
					dim = (int(new_width), int(new_height))
					ratio = dim[0] / float(dim[1])

					image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

					# convert the image to grayscale, blur it, and apply edge detection
					# to reveal the outline of the business card
					gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
					if is_low_contrast(gray, fraction_threshold=self.low_contrast_threshold):
						# update the text and color
						text = "Low contrast: Yes"
						color = (0, 0, 255)

						# improve contrast
						# Adjust the brightness and contrast  
						# g(i,j)=α⋅f(i,j)+β 
						# control Contrast by 1.5 
						alpha = fraction
						# control brightness by 50 
						beta = contrast
						image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta) 
						gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
						print("low")
					else:
						alpha = 1.2  
						# control brightness by 50 
						beta = 80  
						image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta) 
						gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
						print("not so low")


					blurred = cv2.GaussianBlur(gray,(5,5),0) 
					#edged = cv2.Canny(blurred, 30, 150)
					ret, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

					cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

					cnts = imutils.grab_contours(cnts)
					cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
					# initialize a contour that corresponds to the business card outline
					cardCnt = None

					# loop over the contours
					for c in cnts:
						# approximate the contour
						peri = cv2.arcLength(c, True)
						approx = cv2.approxPolyDP(c, 0.02 * peri, True)
						# if this is the first contour we've encountered that has four
						# vertices, then we can assume we've found the business card
						if len(approx) == 4:
							cardCnt = approx
							break
					# if the business card contour is empty then our script could not
					# find the  outline of the card, so raise an error
					if cardCnt is None:
						continue
						raise Exception(("Could not find receipt outline. "
							"Try debugging your edge detection and contour steps."))

					if self.debug:
						print("contrast: ", contrast, "fraction: ", fraction)
						output = image.copy()
						cv2.drawContours(output, [cardCnt], -1, (0, 255, 0), 2)
						cv2.imshow("Business Card Outline", output)
						#cv2.waitKey(0)

					# apply a four-point perspective transform to the *original* image to
					# obtain a top-down bird's-eye view of the business card
					card = four_point_transform(orig, cardCnt.reshape(4, 2) * ratio)
					# show transformed image

					# convert the business card from BGR to RGB channel ordering and then
					# OCR it
					rgb = cv2.cvtColor(card, cv2.COLOR_BGR2RGB)
					text = pytesseract.image_to_string(rgb, lang="deu")

					# use regular expressions to parse out phone numbers and email
					# addresses from the business card
					phoneNums = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
					emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text)
					# attempt to use regular expressions to parse out names/titles (not
					# necessarily reliable)
					nameExp = r"^[\w'\-,.][^0-9_!¡?÷?¿/\\+=@#$%ˆ&*(){}|~<>;:[\]]{2,}"
					names = re.findall(nameExp, text)
					addrExp = r"([\S ]*)[\s,|]*([\S ]+?)\s*(\d+\s*[a-zA-Z]*\s*([-\/]\s*\d*\s*\w?\s*)*)[\s,|]*(\d{5})[\s,|]*([\S ]+)"
					city = re.findall(addrExp, text)
					#print(city)
					#print(text)


					# # show the phone numbers header
					# print("PHONE NUMBERS")
					# print("=============")
					# # loop over the detected phone numbers and print them to our terminal
					# for num in phoneNums:
					# 	print(num.strip())
					# # show the email addresses header
					# print("\n")
					# print("EMAILS")
					# print("======")
					# # loop over the detected email addresses and print them to our
					# # terminal
					# for email in emails:
					# 	print(email.strip())
					# # show the name/job title header
					# print("\n")
					# print("NAME/JOB TITLE")
					# print("==============")
					# # loop over the detected name/job titles and print them to our
					# # terminal
					# for name in names:
					# 	print(name.strip())


					# In[ ]:


					json = {
						"phone": [ num.strip().strip("(").strip(")").strip("-").strip(" ") for num in phoneNums ],
						"name": [ name.strip() for name in names],
						"email": [ email.strip for email in emails ],
						"address": [ line.strip for line in city  ],
						"alpha": fraction,
						"contrast": contrast
					}
					results.append(json)
					
		#pprint(json)
		pprint(self.max_quality_dataset(results))
		return results
	
	def max_quality_dataset(self, data):
		for idx, dataset in enumerate(data):
			score = 0
			for elem in ["phone", "email", "address", "name"]:
				if len(dataset[elem]) == 1:
					score += 10
				elif len(dataset[elem]) > 1:
					score += 5
				if elem[0].strip() != "":
					score += 5
			# bonus points!
			if len(dataset["email"]) > 0 and "@" in dataset["email"][0]:
				score += 15
			if len(dataset["phone"][0] > 0) and len(dataset["phone"][0][0] > 3) and dataset["phone"][0][0].isnumeric():
				score += 15
			dataset["score"] = score
			data[idx] = dataset
		data.sort(key=itemgetter('score'))
		return (max(data, key=lambda x:x['score']))

if __name__ == "__main__":
	arr = glob("attachments/*.*")[-1]
	sorted(arr)
	card = VCardScanner(arr, False)
	print(card.scan_and_ocr())