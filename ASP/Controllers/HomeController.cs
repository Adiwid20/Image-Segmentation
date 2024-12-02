using Microsoft.AspNetCore.Mvc;
using UjiCoba.Models;
using System.Net.Http;
using System.Net.Http.Headers;
using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;
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
        public async Task<IActionResult> UploadImages(UploadImage model)
        {
            if (model.ImageFiles != null && model.ImageFiles.Count > 0)
            {
                var results = new List<string>();

                foreach (var imageFile in model.ImageFiles)
                {
                    var result = await SendImageToFastApi(imageFile);
                    if (result != null)
                    {
                        results.Add(result);
                    }
                }

                ViewBag.SegmentationResults = results; // Simpan hasil segmentasi
                return View("UploadResult");
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
                    return $"data:image/jpeg;base64,{imageBase64}";
                }
                return null;
            }
        }
    }
}