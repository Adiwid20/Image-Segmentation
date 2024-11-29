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
            _fastApiUrl = configuration.GetValue<string>("FastApiUrl"); 

        }
        public IActionResult Index()
        {
            return View();
        }


        [HttpPost]
        public async Task<IActionResult> UploadImage(UploadImage uploadImage)
        {
            if (uploadImage.ImageFile != null && uploadImage.ImageFile.Length > 0)
            {

                var result = await SendImageToFastApi(uploadImage.ImageFile);

                if (result != null)
                {

                    ViewBag.SegmentationResult = result;  
                    return View("UploadResult");
                }
            }
            return View("Index");
        }

        private async Task<string> SendImageToFastApi(IFormFile imageFile)
        {
            var formContent = new MultipartFormDataContent();
            
            using (var ms = new MemoryStream())
            {
                await imageFile.CopyToAsync(ms);
                var byteArray = ms.ToArray();

                var byteContent = new ByteArrayContent(byteArray);
                byteContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/jpeg");


                formContent.Add(byteContent, "file", imageFile.FileName);

                var response = await _httpClient.PostAsync($"{_fastApiUrl}/predict/", formContent);

                if (response.IsSuccessStatusCode)
                {
            
                    var imageBytes = await response.Content.ReadAsByteArrayAsync();
                    var imageBase64 = Convert.ToBase64String(imageBytes);
                    return imageBase64; 
                }
                else
                {
                    return null;
                }
            }
        }
    }
}