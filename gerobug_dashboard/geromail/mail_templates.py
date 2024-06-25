# MAIL TEMPLATES FOR GEROBUG 
# subject_201 = "Your Bug Report Submission is Received"
subject_201 = "Таны тайланг амжилттай хүлээн авлаа."
message_201 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Таны "~TITLE~" гэх тайланг амжилттай хүлээн авлаа, таны тайлангийн ID <b>~ID~</b>
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_202 = "~ID~ тайлангийн төлөв"
message_202 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Имэйл илгээсэнд тань баярлалаа<br><br>

                Таны <b>~ID~</b> (~TITLE~) тайлангийн статус нь <b>~STATUS~</b> шатанд явж байна
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_203 = "~ID~ тайлангийн шинэчлэлтийг амжилттай хүлээн авлаа."
message_203 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Таны <b>~ID~</b> (~TITLE~) тайланг амжилттай шинэчиллээ.
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_204 = "~ID~ тайлангийн талаарх гомдлыг хүлээн авлаа."
message_204 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Таны <b>~ID~</b> (~TITLE~) тайлангийн талаарх гомдлыг хүлээн авлаа.
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_205 = "~ID~ тайлангийн bounty-г зөвшөөрсөнд баярлалаа."
message_205 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Бидний тооцоолсон bounty-г хүлээн зөвшөөрсөнд баярлалаа<br>
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """    

subject_206 = "~ID~ нууцыг задруулахгүй байх гэрээг зөвшөөрсөнд баярлалаа."
message_206 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                <b>~ID~</b> тайлангийн нууцыг задруулахгүй байх гэрээг амжилттай хүлээн авлаа.
                <br>
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_207 = "Таны одоогийн оноо"
message_207 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Манай Bug bounty хөтөлбөрт таны одоогийн оноо <b>~NOTE~</b> байна
                <br>
                Та манай Hall of Fame хуудаснаас нийт оноонуудыг шалгаж болно.
                
                <br><br>
                <b>Stay hungry, stay hunting!</b>
                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_208 = "Тайлангийн статусын тойм"
message_208 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Одоогоор танд манай системд илгээсэн <b>~ID~</b> тайлан байна.
                <br>
                Дэлгэрэнгүй мэдээлэл:
                <br><br>
                
                <table border="1">
                <tr>
                    <th>Report ID</th>
                    <th>Title</th>
                    <th>Status</th>
                </tr>
                ~NOTE~
                </table>
                
                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

# ERROR TEMPLATES FOR GEROBUG
subject_403 = "Таны имэйл хандах эрхгүй байна!"
message_403 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Имэйл илгээсэн тань баярлалаа<br><br>

                Таны имэйл хаяг <b>~ID~</b> тайланд хандах <b>эрхгүй</b> байна.<br>
                Тайлангийн ID 
                <br><br>
                Keep in mind:<br> 
                1. Тайлан илгээсэн имэйл ашиглана уу<br>
                2. Илгээсэн тайлангийн ID-г дахин шалгана уу<br>
                3. Тодорхой хүсэлт гаргахаас өмнө урьдчилсан зааварчилгааг хүлээнэ үү<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_404 = "ХҮЧИНГҮЙ REPORT"
message_404 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Имэйл илгээсэнд тань баярлалаа<br><br>

                Таны илгээсэн имэйл амжилтгүй боллоо
                <br>
                Учир нь:<br> 
                <b>~NOTE~</b>
                <br>
                Таны имэйл стандарт, форматыг хангаж байгаа эсэхийг <a href="https://bugbounty.mn/submit" target="_blank">эндээс</a> шалгана уу <br>


                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_405 = "INVALID REPORT ID"
message_405 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Имэйл илгээсэнд тань баярлалаа<br><br>
                Таны илгээсэн (<b>~ID~</b>) тайлан ХҮЧИНГҮЙ байна
                <br> 
                Тайлангийн ID-аа зөв ​​эсэхийг шалгана уу.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_406 = "Энэ имэйл хар жагсаалтад орсон байна"
message_406 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Энэ имэйл SPAM ACTIVITY-ийн улмаас <b>ХАР ЖАГСААЛТАД</b> орсон байна

                Та <b>~NOTE~</b> секундийн дараа хар жагсаалтаас гарах болно.
                <br> 
                Дээрх хугацаа дууссаны дараа дахин имэйл илгээх боломжтой.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """


# NOTIFICATION TEMPLATES FOR GEROBUG
subject_300 = "~ID~ тайланд зориулсан мэдэгдэл"
message_300 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>

                Энэхүү имэйлээрээ бид танд (~TITLE~)<br>
                <b>~ID~</b> тайлангийн статусыг танилцуулж байна.<br>
                Таны тайлангийн статус: <b>~STATUS~</b>
                <br>
                Учир нь:<br> 
                <b>~NOTE~</b>

                <br><br>
                Манай системийг аюулгүй ажиллагаанд хувь нэмрээ оруулсанд тань баярлалаа.
                <br><br>
                
                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_301 = "~ID~ тайланд зориулсан мэдэгдэл"
message_301 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>

                Энэхүү имэйлээрээ бид танд (~TITLE~)<br>
                <b>~ID~</b> тайлангийн статусыг танилцуулж байна.<br>
                Таны тайлангийн статус: <b>~STATUS~</b>
                <br> 
                Тун удахгүй тань руу хариу имэйл илгээх учир та түр хүлээнэ үү.<br>

                <br><br>

                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """



# REQUEST TEMPLATES FOR GEROBUG
subject_701 = "~ID~ тайлангийн талаар нэмэлт мэдээлэл хүсэх нь"
message_701 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Энэхүү имэйлээрээ бид <b>~ID~</b> (~TITLE~) тайлангийн<br>
                талаар илүү дэлгэрэнгүй мэдээлэл авахыг хүсэж байна.<br>

                <br>
                Тайлбар:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Та одоогийн имэйл хаягаа ашиглан "<b>UPDATE_~ID~</b>" гарчигтайгаар шинэчилсэн тайлангаа илгээж болно<br>
                Имэйлийн үндсэн хэсэгт шинэчлэлтүүдийг <b>нэгтгэн</b>-г оруулна уу (зөвхөн текст)<br>
                <b>PDF файлаа хавсаргахаа бүү мартаарай</b><br>
                
                <br>Имэйлийн форматын талаар нэмэлт мэдээлэл авахыг хүсвэл манай нүүр хуудаснаас харж болно<br>
                
                <br><br>
                Бид таны санал хүсэлтийг хүлээж байна<br>
                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_702 = "~ID~ тайлангийн bounty-г тооцоолох"
message_702 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Энэхүү имэйлээр бид танд <b>~ID~</b> (~TITLE~) тайлангийн
                шагналын тооцооны талаар мэдэгдэхийг хүсэж байна.<br>
                
                <br>
                Эмзэг байдлын зэрэг (Severity): <b>~SEVERITY~</b><br>

                <br>
                Тайлбар:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Хэрэв та bounty-ний тооцооллыг хүлээн зөвшөөрч байвал subject хэсэгт "<b>AGREE_~ID~</b>" гэсэн имэйлийг ямар нэгэн илүү текстийг үндсэн хэсэгт агуулалгүй илгээнэ үү.<br>
                <br>
                Хэрэв та bounty-ний тооцоололтой санал нийлэхгүй байвал subject хэсэгт "<b>APPEAL_~ID~</b>" гэсэн имэйлийг илгээх ба үндсэн хэсэгт шалтгаан/тайлбарыг нэмнэ үү (зөвхөн текст)<br>

                Та <b>3 удаа</b> заргалдах хязгаартай, эс тэгвээс бид таныг зөвшөөрсөн гэж үзэн асуудлыг шийдвэрлэнэ.
                <br>
                
                <br>Имэйлийн форматын талаар нэмэлт мэдээлэл авахыг хүсвэл манай нүүр хуудаснаас харж болно<br>

                <br><br>
                Бид таны санал хүсэлтийг хүлээж байна<br>
                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_703 = "~ID~ урьдчилсан нөхцөл, нууцыг задруулахгүй байх гэрээ (NDA)"
message_703 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Энэхүү имэйлээр бид танд <b>~ID~</b> (~TITLE~) тайлангийн
                шагналыг тооцоолоход шаардлагатай мэдээллийг хүсэхийг хүсэж байна.<br>

                <br>
                Тайлбар:<br> 
                <b>~NOTE~</b>
                
                <br><br>

                Та одоогийн имэйл хаягаа ашиглан "<b>NDA_~ID~</b>" гарчигтайгаар имэйл илгээнэ үү<br>
                Нэмэлт хүсэлтийг имэйлийн үндсэн хэсэгт нэмнэ үү (зөвхөн текст)<br>
                <b>signed NDA</b> буюу гарын үзэг зурсан файлаа хавсаргахаа бүү мартаарай<br>
                
                <br>Имэйлийн форматын талаар нэмэлт мэдээлэл авахыг хүсвэл манай нүүр хуудаснаас харж болно<br>

                <br><br>
                Бид таны санал хүсэлтийг хүлээж байна<br>
                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """

subject_704 = "Thank you for your contribution"
message_704 = """\
        <html><body>
            <p>
                Сайн байна уу,<br>
                Энэхүү имэйлээр бид таны bounty-г боловсруулж дууссаныг мэдэгдэхийг хүсэж байна<br>
                <br>
                Тайлбар:<br> 
                <b>~NOTE~</b>
                
                <br><br>

                Таны <b>~ID~</b> (~TITLE~) тайлан бидний аюулгүй байдалд үнэтэй хувь нэмэр оруулсанд талархаж байна.
                
                <br> 
                Stay hungry, Stay hunting!<br>

                <br><br>
                Хүндэтгэсэн,<br>
                Bugbounty.mn
            </p>
        </body></html>
        """



# DICTIONARY VARIABLES
subjectlist = {
    201: subject_201,   # SUBMIT SUCCESS (TITLE, ID)
    202: subject_202,   # CHECK STATUS SUCCESS (TITLE, ID, STATUS)
    203: subject_203,   # UPDATE SUCCESS (TITLE, ID)
    204: subject_204,   # APPEAL SUCCESS (TITLE, ID)
    205: subject_205,   # AGREE SUCCESS (ID)
    206: subject_206,   # NDA SUCCESS (ID)
    207: subject_207,   # CHECK SCORE (NOTE)
    208: subject_208,   # CHECK ALL STATUS (ID, NOTE)

    300: subject_300,   # INVALID NOTIFICATION (TITLE, ID, STATUS, NOTE)
    301: subject_301,   # STATUS UPDATE NOTIFICATION (TITLE, ID, STATUS)
    
    403: subject_403,   # UNAUTHORIZED (ID)
    404: subject_404,   # INVALID FORMAT
    405: subject_405,   # INVALID REPORT ID (ID)
    406: subject_406,   # BLACKLIST (NOTE)

    701: subject_701,   # REQUEST UPDATE/AMEND (TITLE, ID, NOTE, URL)
    702: subject_702,   # SEND BOUNTY CALCULATIONS (TITLE, ID, NOTE, URL)
    703: subject_703,   # REQUEST NDA (TITLE, ID, NOTE, URL)
    704: subject_704    # SEND BOUNTY + PROOF (TITLE, ID)
}

messagelist = {
    201: message_201,
    202: message_202,
    203: message_203,
    204: message_204,
    205: message_205,
    206: message_206,
    207: message_207,
    208: message_208,

    300: message_300,
    301: message_301,

    403: message_403,
    404: message_404,
    405: message_405,
    406: message_406,

    701: message_701,
    702: message_702,
    703: message_703,
    704: message_704
}
