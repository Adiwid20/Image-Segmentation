using Microsoft.AspNetCore.Http;

namespace UjiCoba.Models
{
    public class UploadImage
    {
        public List<IFormFile> ImageFiles { get; set; } = new List<IFormFile>();
    }
}