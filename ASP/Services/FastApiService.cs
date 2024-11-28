using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;

namespace ASP.Services
{
    public class FastApiService
    {
        private readonly HttpClient _httpClient;

        public FastApiService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public async Task<string> SendImageForSegmentation(IFormFile image)
        {
            var formData = new MultipartFormDataContent();
            var fileContent = new ByteArrayContent(await GetImageBytes(image));
            fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/png");

            formData.Add(fileContent, "file", image.FileName);

            var response = await _httpClient.PostAsync("http://localhost:8000/predict/", formData);

            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadAsStringAsync();
                return result;  
            }

            return null;
        }

        private async Task<byte[]> GetImageBytes(IFormFile image)
        {
            using (var memoryStream = new System.IO.MemoryStream())
            {
                await image.CopyToAsync(memoryStream);
                return memoryStream.ToArray();
            }
        }
    }
}