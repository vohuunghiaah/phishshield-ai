# Câu hỏi phản biện PhishShield AI

*Bản công khai Gate 7. Các bảng theo mẫu được tổng hợp để bảo vệ dữ liệu nghiên cứu.*

82 câu hỏi và trả lời • Hồ sơ bảo vệ của Gịp Xương Thanh Quyền, Vũ Thị Tuyết Trang và Võ Hữu Nghĩa.

## Dataset

**1. Vì sao chọn CompPhish v4?**

Một bản phát hành liên kết URL, snapshot, nhãn và định danh. Nhờ vậy có thể thử 17 và 34 biến trên cùng trang, kiểm SHA các tệp nguồn và công bố cohort chính xác của nghiên cứu.

**2. Một quan sát đại diện cho cái gì?**

Một mẫu website theo serial_number và snapshot lúc thu thập. Nhiều mẫu có thể liên hệ qua domain hoặc nội dung HTML.

**3. Tỷ lệ nhãn đầu vào ra sao?**

Trong 15.358 mẫu có 8.154 hợp lệ và 7.204 phishing. Tỷ lệ đó thuộc corpus và sẽ khác tỷ lệ gặp trong lưu lượng sử dụng thực tế.

**4. Vì sao hai modality có cùng số hàng?**

Cohort so sánh yêu cầu cả URL lẫn HTML dùng được. Điều này kiểm soát thành phần mẫu, đồng thời làm giảm đại diện cho những website thường không lấy được snapshot.

## Tiền xử lý

**5. Có bao nhiêu mẫu bị loại?**

31 mẫu gồm 23 URL không hợp lệ và tám HTML rỗng. 15.327 mẫu còn lại xuất hiện trong Train, Validation hoặc Test.

**6. Gặp HTML rỗng ở ứng dụng thì sao?**

Nếu người dùng gửi một trường HTML rỗng hoặc chỉ có khoảng trắng, API trả 422. Khi người dùng chỉ gửi URL, API chủ động chọn checkpoint 17 biến.

**7. Đã xác minh quan hệ giữa tệp bằng cách nào?**

Kiểm checksum tám tệp nguồn, đối chiếu định danh, nhãn, URL, snapshot và bản trích đặc trưng. Bảng T02 ghi không có snapshot mồ côi hoặc thiếu.

**8. Vì sao giữ số liệu trùng lặp trong audit?**

Bảy dòng trùng URL và 2.178 dòng trùng snapshot cho biết nguy cơ dữ liệu liên quan nằm ở hai tập. Dấu vết này cho phép xem lại việc tạo nhóm và kiểm giao tập.

## EDA

**9. Vì sao khám phá phân bố trên Train?**

Các quyết định về đặc trưng có thể chịu ảnh hưởng khi nhìn thấy holdout. Hình F04 và F05 dùng phần Train, còn Test dành cho đánh giá đã khóa.

**10. Tương quan Spearman đo gì?**

Liên hệ đơn điệu giữa thứ hạng hai biến. Số thẻ và số liên kết có thể cùng phản ánh kích thước trang. Tương quan không xác lập biến nào gây ra nhãn.

**11. Một trang nhiều thẻ liệu có hợp lệ?**

Có 147 cảnh báo nhầm và 17 trường hợp bỏ sót trên Test. Phân tích nội bộ ghi nhận cả lỗi sát ngưỡng và lỗi ở xa ngưỡng. Bảng công khai trình bày kết quả tổng hợp theo loại dự đoán.

**12. Cần đọc phân bố lớp ở cấp nào?**

Cả mẫu và nhóm. Ba fold đều có 2.537 nhóm nhưng tỷ lệ phishing từ 37,64% đến 51,41%, nên cân bằng số nhóm chưa bảo đảm cân bằng lớp.

## Kỹ thuật đặc trưng

**13. Vì sao dùng 34 biến thay vì 70?**

34 biến có hàm tính tái dùng cho từng yêu cầu chỉ có URL và HTML tĩnh, cùng schema có thứ tự. Bảng 70 biến đi kèm corpus cho phép đối chiếu, nhưng việc dùng hết cần chứng minh có đầu vào tương ứng khi phục vụ.

**14. Tại sao thử hai modality?**

Người dùng có thể chỉ có URL. Thiết kế hai nhánh vừa lượng hóa ảnh hưởng thực nghiệm của HTML, vừa cung cấp checkpoint hoạt động đúng khi thiếu snapshot.

**15. Tại sao không điền số 0 vào 17 cột HTML còn thiếu?**

Số 0 đã có nghĩa quan sát được, chẳng hạn trang có 0 thẻ form. Dùng checkpoint URL-only giữ đúng phân bố đầu vào và ngưỡng được đánh giá cho tình huống thiếu HTML.

**16. Schema chứa những gì hữu ích khi tái lập?**

Phiên bản và danh sách cột đúng thứ tự của mỗi modality. Một vector đủ 34 số vẫn có thể dẫn tới sai dự đoán nếu đổi chỗ hai biến.

**17. HTTPS đủ xác nhận an toàn không?**

HTTPS chỉ là một đặc trưng lexical. Mô hình còn xem URL và cấu trúc trang, và chính ứng dụng hiển thị lưu ý rằng HTTPS đơn lẻ không bảo đảm an toàn.

## Rò rỉ dữ liệu

**18. Vì sao dùng group split?**

Các URL cùng domain hoặc snapshot trùng có thể mang dấu hiệu gần như nhau. Chia nguyên nhóm làm khó việc nhớ lại những dấu hiệu này. Audit kiểm tra giao của URL, domain và exact HTML hash qua các tập.

**19. Hồ sơ nào xác định đúng split?**

Chỉ mục đã khóa và manifest SHA-256 đi cùng. Thay một dòng có thể làm hash sai dù tổng số dòng và tỷ lệ nhãn vẫn đúng.

**20. StandardScaler phải học ở đâu?**

Trên phần dữ liệu dùng để học trọng số. Outer-validation, Validation chính thức và Test chỉ được biến đổi bằng tham số tương ứng đã học.

**21. Group split có loại trừ mọi rò rỉ?**

Các kiểm tra bao phủ định danh và quan hệ nhóm đã định nghĩa. Template sửa nhẹ, họ chiến dịch hoặc nhãn nhiễu vẫn có thể tạo phụ thuộc xuyên tập.

## Random Forest

**22. Tại sao chọn 300 cây?**

Candidate thắng OOF của hai nhánh đều có 300 cây trong tập giá trị đã thử. C022 URL và C019 URL+HTML còn khác giới hạn lá, độ sâu và tham số lấy mẫu biến. Kết quả hỗ trợ hai cấu hình hoàn chỉnh trong ngân sách 24 candidate mỗi nhánh.

**23. Đầu ra của rừng là gì?**

Các cây trả xác suất lớp tại lá, rồi rừng lấy trung bình. Service lấy cột xác suất phishing, so với ngưỡng của chính bundle.

**24. Tại sao giới hạn độ sâu ở nhánh URL?**

C022 chọn max_depth 10 và min_samples_leaf 4. Giới hạn này làm các vùng lá bớt chi tiết trên 17 biến. Hiệu quả riêng của độ sâu phải đọc từ sweep kiểm soát.

**25. Vì sao RF chạy CPU?**

Estimator scikit-learn đã khóa dùng CPU, cấu hình n_jobs cho phép song song. Manifest ghi thiết bị thực đã chạy. Nghiên cứu chưa đo chênh lệch tốc độ CPU/GPU của RF.

## XGBoost

**26. Vì sao số cây khác nhau giữa hai modality?**

C006 chọn 100 vòng trên URL, C004 chọn 300 trên URL+HTML. OOF đo các cấu hình trong hai không gian biểu diễn khác nhau. Learning rate, độ sâu và regularization cùng quyết định hiệu quả của số vòng.

**27. Ba seed giống điểm có phải lặp một file?**

Mỗi run có attempt, manifest và checkpoint riêng. Inventory ghi cả hash cây và hash vector Validation để phân biệt việc lặp đầu ra với việc tái sử dụng đường dẫn.

**28. Vì sao XGBoost có thể ít nhạy với seed?**

Cấu hình hist thực nghiệm dùng subsample và colsample_bytree bằng 1. Không lấy ngẫu nhiên bớt hàng/cột làm giảm nguồn biến thiên ở cùng đầu vào và môi trường.

**29. Tại sao XGBoost cũng chạy CPU?**

Workflow chốt backend hist và môi trường CPU cho họ cây. T07 ghi thiết bị thực của từng run. Không có cặp benchmark chuyên biệt để kết luận GPU nhanh hay chậm hơn.

## MLP

**30. Kiến trúc nào đã được đo?**

Một lớp ẩn ReLU, đầu ra logit nhị phân. Baseline dùng 64 nút, cả hai winner C021 dùng 256. Schema đầu vào có 17 hoặc 34 chiều.

**31. Tại sao dùng BCEWithLogitsLoss?**

Classifier học trực tiếp từ logit nhị phân với hàm mất mát ổn định số. Chuyển logit thành điểm để đánh giá theo ngưỡng ở bước dự đoán.

**32. Early stopping ảnh hưởng so sánh thế nào?**

Outer train còn phải dành dữ liệu cho việc dừng. Ở C021 URL+HTML fold 0, 5.379 dòng fit và 2.316 dòng dừng, khác số mẫu thực học của cây.

**33. Bản demo có dùng GPU để giải thích không?**

Hai checkpoint triển khai là RF CPU. Việc MLP từng học trong môi trường riêng được ghi ở T07 và không tạo yêu cầu GPU cho inference của ứng dụng.

## Tối ưu siêu tham số

**34. Tại sao tuning có thể làm kết quả giảm?**

Winner tối ưu OOF trên Train với một seed và ngân sách hữu hạn. Validation chứa các nhóm khác và chọn ngưỡng cho checkpoint sau refit. XGBoost URL giảm 1,023 điểm F2 và tăng 10,229 điểm FPR trên Validation.

**35. Một trial gồm bao nhiêu phép đánh giá?**

Ba outer fold tạo ba vector con ngoài fold. Gộp chúng để chấm một candidate trên toàn bộ 10.729 dòng Train.

**36. Controlled sweep khác một winner phối hợp thế nào?**

Trong sweep có kiểm soát chỉ tham số đang xét thay đổi. Winner có thể đổi nhiều tham số cùng lúc, nên không thể gán toàn bộ chênh lệch cho một tham số.

**37. Có phải đã tìm tối ưu toàn cục?**

Mỗi cặp có 24 candidate theo thiết kế khóa. Kết quả chỉ xác định lựa chọn tốt nhất theo luật xếp hạng trong các candidate đã đánh giá.

## Cross-validation

**38. Tại sao dùng ba fold?**

Thiết kế khóa dành ba phần nhóm cho mỗi candidate và giữ mỗi mẫu Train làm ngoài fold một lần. Số lượt chạy bằng 144 × 3 = 432.

**39. Vì sao không lấy trung bình số học F2 của ba fold?**

Fold có số hàng và tỷ lệ lớp khác nhau. F2 là hàm phi tuyến của các ô ma trận, nên F2 từ toàn bộ OOF khác trung bình F2 từng fold.

**40. Có dùng Test để chọn candidate không?**

Candidate chỉ nhìn OOF thuộc Train. Selection sử dụng Validation sau refit, và Test chỉ xuất hiện sau khi leader duyệt.

**41. Làm sao nhận biết sai fold dù metric trông hợp lý?**

So serial_number, fold và nhãn của toàn bộ OOF với chỉ mục CV khóa. Tính lại metric từng fold tại cùng ngưỡng gộp cho từng candidate.

## Chỉ số đánh giá

**42. Tại sao F2 là primary metric?**

Vì ưu tiên phát hiện phishing bị bỏ sót. F2 bằng 5TP/(5TP+4FN+FP). FPR và Precision vẫn cần báo để người đọc định lượng chi phí của ưu tiên này.

**43. Tại sao Recall cao nhưng FPR cũng lớn?**

Ngưỡng 0,20 khiến nhiều điểm trung bình được cảnh báo. Trong 1.077 mẫu phishing chỉ 17 bị bỏ sót, nhưng 147/1.222 mẫu hợp lệ vượt ngưỡng. Hai tỷ lệ có mẫu số khác nhau.

**44. Precision trả lời câu hỏi nào?**

Trong 1.207 cảnh báo của primary, 1.060 là phishing. Tỷ lệ 87,82% phụ thuộc cả tỷ lệ lớp tại dữ liệu sử dụng.

**45. PR-AUC và average precision có giống nhau?**

Tích phân hình thang của đường PR và tổng precision theo bước tăng recall cho hai ước lượng khác nhau. Trên Test chúng lần lượt xấp xỉ 0,989479 và 0,989484.

**46. Accuracy có che khuất điều gì?**

92,87% không cho biết loại sai nào nhiều. Việc tách 147 FP và 17 FN giúp đánh giá rõ chi phí nghiệp vụ.

## Ngưỡng

**47. Vì sao threshold 0,20?**

Trên Validation của primary seed 43, F2 đạt khoảng 95,97% tại 0,20, cao hơn 95,69% tại 0,25. Quy tắc quét các mức 0,05 đến 0,95 đã chọn ngưỡng trước Test.

**48. Vì sao fallback sử dụng 0,15?**

Đó là ngưỡng được chọn trên Validation của RF URL-only seed 44. Phân bố điểm và thông tin đầu vào khác primary nên ngưỡng được lưu riêng trong registry.

**49. Nếu điểm đúng bằng ngưỡng thì sao?**

Quy tắc dùng dấu lớn hơn hoặc bằng. Kiểm thử với estimator điểm cố định xác minh bằng ngưỡng cho nhãn 1.

**50. Có thể giảm FPR bằng cách chỉnh ngưỡng bây giờ?**

Thay điểm vận hành cần một giao thức và tập chọn ngưỡng mới. Giao thức hiện hành giữ nguyên 0,20 và báo trung thực các cảnh báo nhầm trên Test.

## Chọn mô hình

**51. Vì sao không chọn baseline XGBoost dù F2 cao hơn?**

Tập ứng viên của quyết định triển khai đã khóa ở pha TUNED_V2. XGBoost baseline đạt 96,048% ở Validation và được báo để so sánh. Đưa nó trở lại sau khi thấy kết quả sẽ thay câu hỏi lựa chọn.

**52. RF có thực sự tốt hơn XGBoost?**

Trong các nhánh tuned URL+HTML, RF hơn xấp xỉ 0,020 điểm F2 trung bình. Thiết kế dùng một split và không đánh Test đối chứng XGBoost, nên chưa đủ kết luận ưu thế tổng quát.

**53. Tại sao chọn seed 43 cho primary?**

Sau khi xếp các cặp bằng mean Validation, giao thức xếp từng run trong nhóm thắng theo F2, precision, FPR và seed. Run thắng là RF URL+HTML seed 43.

**54. Ai duyệt Test?**

Hồ sơ phê duyệt ghi Vohuunghia, tức Võ Hữu Nghĩa, trưởng nhóm. SHA của selection được đối chiếu trước khi dùng kết quả Test.

## Thống kê

**55. Vì sao dùng ba seed?**

42, 43, 44 đo độ nhạy với khởi tạo hoặc lấy mẫu nội tại trên cùng split trong ngân sách của nhóm. Ba seed không đại diện cho ba corpus độc lập.

**56. Ghép theo seed có ý nghĩa gì?**

Lấy V2 trừ V1 ở cùng mô hình, modality, split và seed, rồi tổng hợp ba hiệu. T17 cho phép kiểm từng cặp trước khi đọc trung bình ở T19.

**57. Độ lệch chuẩn dùng mẫu số nào?**

Với ba seed, độ lệch chuẩn mẫu chia cho hai khi tính phương sai. Số này mô tả phân tán quan sát và không phải khoảng tin cậy của F2 trên website mới.

**58. Hiệu ứng nào ổn định nhất?**

Ở baseline, thêm HTML tăng F2 6,005 điểm với RF, 6,289 với XGBoost và 6,599 với MLP. Bốn trong sáu cặp V1–V2 giảm F2 sau tuning.

## Explainable AI

**59. SHAP giải thích được gì?**

Nó phân bổ chênh lệch giữa điểm của checkpoint và mức nền theo các biến. Trên 24 mẫu Validation, anchor_count đứng đầu theo mean absolute SHAP, khoảng 0,1040.

**60. SHAP có chứng minh nguyên nhân phishing?**

Không. Nó mô tả hàm đã học với nền 32 mẫu Train. Các biến tương quan có thể chia sẻ đóng góp, và nhãn thực tế còn phụ thuộc nội dung ngoài vector đặc trưng.

**61. Kiểm toán SHAP như thế nào?**

Đối chiếu ID và thứ tự cột, tính lại điểm nền và điểm từng dòng bằng checkpoint. Tổng 34 đóng góp cộng nền sai khác tối đa khoảng 1,78 × 10⁻¹⁵, rồi đối chiếu trung bình trị tuyệt đối theo biến.

**62. Giải thích trên API khác gì?**

Service thay tuần tự từng biến từ trung vị Train, lấy hiệu điểm và trả tối đa năm biến đóng góp lớn nhất. Hiệu phụ thuộc thứ tự cột. Tên phương pháp có trong JSON.

## REST API

**63. Mô hình được triển khai thế nào?**

Uvicorn phục vụ FastAPI trên loopback. API đối chiếu registry, checksum bytes, schema, model và modality trước khi dùng joblib, sau đó chạy predict_proba và áp dụng ngưỡng khóa.

**64. Health và ready khác nhau thế nào?**

Health xác nhận tiến trình trả lời. Ready thử tải primary và fallback, nên có thể trả 503 trong khi health vẫn 200.

**65. Làm sao xác minh API không giả mạo kết quả?**

Requests gửi ví dụ kiểm soát tới Uvicorn thật. Script so nhãn, score, threshold, model_version, modality và các đóng góp với inference offline. Log lưu các yêu cầu và HTTP status.

**66. Checkpoint primary lỗi có đổi sang fallback?**

Service trả lỗi 503. Việc chọn nhánh phụ thuộc dữ liệu đầu vào. Sự cố hệ thống có thể được quan sát qua ready và không bị che bởi một quyết định khác.

## Giao diện

**67. Làm sao biết frontend dùng REST thực?**

Playwright thao tác trình duyệt Streamlit đang chạy. Hai lần phân tích trả đúng nhãn nhánh và tạo POST tương ứng trong access log Uvicorn.

**68. Khi API ngừng, người dùng thấy gì?**

UI hiển thị thông báo không kết nối được. AppTest trỏ sang cổng không có dịch vụ, nhấn phân tích và kiểm nội dung lỗi.

**69. Mục hiệu năng lấy dữ liệu ở đâu?**

Nó gọi GET /performance. Backend đọc kết quả Test và đối chiếu danh tính primary với registry trước khi trả số liệu.

**70. Điểm thấp nên hiểu thế nào?**

Mẫu chưa vượt ngưỡng cảnh báo của checkpoint dùng trong yêu cầu. Điểm chưa được hiệu chỉnh và vẫn có 17 trường hợp bỏ sót trên Test.

## An toàn hệ thống

**71. Ứng dụng có ghé thăm trang người dùng nhập không?**

Bản demo tắt live fetch và khởi động với isolated egress bằng 0. Input chỉ được xử lý cục bộ. Ví dụ E2E dùng example.org và snapshot tự tạo.

**72. HTML chứa script có chạy không?**

HTML được phân tích tĩnh để đếm đặc trưng. UI trình bày kết quả mô hình. Kiểm thử với thẻ script giữ được luồng phân tích mà không cần thực thi nội dung trang.

**73. Đầu vào quá lớn bị xử lý ở đâu?**

ASGI giới hạn dung lượng thân request, kể cả khi truyền theo khối. API giới hạn nội dung HTML 8 MiB theo UTF-8. Vượt giới hạn trả 413.

**74. Checksum có đủ bảo vệ khỏi mọi trường hợp?**

Digest phát hiện bytes sai so với registry tin cậy. Người vận hành cần kiểm soát quyền sửa registry và checkpoint, vì bên thay được cả hai có thể thay cả giá trị đối chiếu.

## Hạn chế

**75. Hệ thống có phát hiện website phishing chưa từng thấy?**

Nó gán điểm cho URL hoặc snapshot mới theo schema. Group holdout kiểm tra các nhóm chưa học trong CompPhish. Khả năng phát hiện theo thời gian, trên corpus khác hoặc chiến dịch mới chưa được đo độc lập.

**76. Hệ thống có phải Generative AI?**

Đây là phân loại có giám sát trên đặc trưng dạng bảng. Nội dung giải thích đến từ đóng góp số và văn bản có sẵn. Hệ thống không sinh HTML hay dùng mô hình ngôn ngữ để phán đoán URL.

**77. Kết quả Test của fallback là bao nhiêu?**

Thiết kế khóa chỉ chấm primary trên Test. Fallback có điểm Validation, kiểm tra checksum và bằng chứng inference. Không lấy số primary gán cho fallback.

**78. Điều kiện nào còn thiếu để triển khai rộng?**

Cần đánh giá ngoại bộ và theo thời gian, hiệu chỉnh điểm nếu muốn diễn giải xác suất, đo tải đồng thời và thẩm định kiểm soát vận hành trên môi trường đích.

**79. Đóng góp có thể tái sử dụng ngay là gì?**

Có thể tái tạo 28 bảng, 30 hình từ artifact khóa, tra cứu 36 run và 144 candidate, rồi chạy hai nhánh API cục bộ với đúng checkpoint đã duyệt.

**80. Độ chính xác trên tập Test có áp dụng cho API mọi lúc không?**

Không thể suy ra điều đó. Chỉ số đã đo thuộc primary với snapshot và tỷ lệ lớp của holdout. API có thể nhận URL-only, trang mới hoặc tập người dùng có phân bố khác.

**81. Tại sao latency trên bảng T25 có ô trống?**

Một số run baseline không lưu thời gian fit và inference độc lập. Bảng dùng NOT_AVAILABLE để người đọc phân biệt dữ liệu thiếu với thời gian bằng 0.

**82. Nếu cần kiểm tra lại số liệu thì bắt đầu ở đâu?**

Chạy scripts/generate_final_analysis.py bằng môi trường khóa với các extra phân tích. Script kiểm SHA, replay Validation và tái tính từ OOF/Test đã lưu trước khi xuất bảng và hình. Mọi kết quả phát sinh nằm trong reports/final.

[Nguồn số liệu và quy tắc](PHISHSHIELD_AI_EXPERIMENT_PROTOCOL_AND_ANALYSIS.md) · [Kiểm toán thực nghiệm](../../reports/final/FINAL_EXPERIMENT_AUDIT.md) · [Bằng chứng HTTP](../../reports/product/http_evidence.json)

