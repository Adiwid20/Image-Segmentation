using Microsoft.AspNetCore.Mvc;
using UjiCoba.Models;
using System.Net.Http;
using System.Net.Http.Headers;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;

namespace ASP.Controllers
{
    public class HomeController : Controller
    {
        private readonly HttpClient _httpClient;
        private readonly string _fastApiUrl;

        public HomeController(HttpClient httpClient, IConfiguration configuration)
        {
            _httpClient = httpClient;
            _fastApiUrl = configuration.GetValue<string>("FastApiUrl"); // Pastikan URL FastAPI sudah diset di appsettings.json
        }

        // Action untuk halaman utama (form upload gambar)
        public IActionResult Index()
        {
            return View();
        }

        // Action untuk memproses gambar yang di-upload
        [HttpPost]
        public async Task<IActionResult> UploadImage(UploadImage uploadImage)
        {
            if (uploadImage.ImageFile != null && uploadImage.ImageFile.Length > 0)
            {
                // Kirim gambar ke FastAPI untuk segmentasi
                var result = await SendImageToFastApi(uploadImage.ImageFile);

                if (result != null)
                {
                    // Kirim hasil segmentasi ke view
                    ViewBag.SegmentationResult = result;  // Bisa berupa URL atau path gambar hasil segmentasi
                    return View("UploadResult");
                }
            }
            return View("Index");
        }

        private async Task<string> SendImageToFastApi(IFormFile imageFile)
        {
            var formContent = new MultipartFormDataContent();
            
            // Convert IFormFile to byte array
            using (var ms = new MemoryStream())
            {
                await imageFile.CopyToAsync(ms);
                var byteArray = ms.ToArray();

                // Create a ByteArrayContent from the byte array and set the content type
                var byteContent = new ByteArrayContent(byteArray);
                byteContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/jpeg");

                // Add to multipart content
                formContent.Add(byteContent, "file", imageFile.FileName);

                // Send the request to FastAPI
                var response = await _httpClient.PostAsync($"{_fastApiUrl}/predict/", formContent);

                if (response.IsSuccessStatusCode)
                {
                    // Read the response (image)
                    var imageBytes = await response.Content.ReadAsByteArrayAsync();
                    var imageBase64 = Convert.ToBase64String(imageBytes);
                    return imageBase64; // Return the base64 string of the image
                }
                else
                {
                    return null;
                }
            }
        }
    }
}